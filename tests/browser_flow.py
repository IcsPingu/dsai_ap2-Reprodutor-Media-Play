"""Verificação opcional: python tests/browser_flow.py (Playwright + soundfile).

O servidor é iniciado e encerrado pelo teste. Dados reais nunca são usados.
"""

import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

from playwright.sync_api import expect, sync_playwright
import soundfile as sf


PROJECT = Path(__file__).resolve().parents[1]
ARTIFACTS = Path(tempfile.gettempdir()) / "opencode" / "unified-music-verification"
ARTIFACTS.mkdir(parents=True, exist_ok=True)


def choose_rule_option(page, key, label):
    """Selecionar pelo widget, após salvar entradas de texto que causam rerun."""
    try:
        container = page.locator(f".st-key-{key}")
        widget = container.get_by_role("combobox")
        expect(widget).to_be_visible()
        expect(page.get_by_test_id("stApp")).to_have_attribute(
            "data-test-script-state", "notRunning"
        )
        # React Aria usa input de busca. Confirmar a opção real (não apenas texto
        # digitado) é necessário para enviar o valor ao servidor.
        widget.fill(label)
        if widget.get_attribute("aria-expanded") != "true":
            container.locator('button[aria-haspopup="listbox"]').click()
        expect(page.get_by_role("option", name=label, exact=True)).to_be_visible()
        widget.press("ArrowDown")
        widget.press("Enter")
        expect(widget).to_have_value(label)
        expect(page.get_by_test_id("stApp")).to_have_attribute(
            "data-test-script-state", "notRunning"
        )
    except Exception:
        page.screenshot(path=str(ARTIFACTS / "failure.png"), full_page=True)
        (ARTIFACTS / "failure.html").write_text(page.content(), encoding="utf-8")
        raise


def main():
    errors = []
    checks = []
    with tempfile.TemporaryDirectory(dir=ARTIFACTS) as folder:
        root = Path(folder)
        media = []
        for extension in ("mp3", "wav", "flac"):
            path = root / f"Silent test.{extension}"
            sf.write(path, [0.] * (16000 * 30), 16000, format=extension.upper())
            media.append(str(path))
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        env = dict(os.environ, MEDIA_PLAY_DATA=str(root / "private"),
                   STREAMLIT_BROWSER_GATHER_USAGE_STATS="false", PYTHONDONTWRITEBYTECODE="1")
        with open(ARTIFACTS / "server.log", "w", encoding="utf-8") as log:
            server = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", "app.py",
                "--server.headless=true", "--server.address=127.0.0.1",
                "--server.fileWatcherType=none",
                f"--server.port={port}",
            ], cwd=PROJECT, env=env, stdout=log, stderr=subprocess.STDOUT)
            try:
                url = f"http://127.0.0.1:{port}"
                for _ in range(100):
                    try:
                        with urlopen(url + "/_stcore/health", timeout=1) as response:
                            if response.status == 200:
                                break
                    except OSError:
                        time.sleep(0.1)
                else:
                    raise RuntimeError("Servidor não iniciou; consulte server.log")
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(
                        executable_path=os.environ.get("BROWSER_EXECUTABLE") or None,
                        args=["--autoplay-policy=no-user-gesture-required"],
                    )
                    page = browser.new_page(viewport={"width": 1600, "height": 1200})
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    page.goto(url)
                    page.get_by_label("Usuário", exact=True).fill("mixed_browser")
                    page.get_by_label("Senha", exact=True).fill("temporary-browser-test-password")
                    page.get_by_text("Criar conta", exact=True).click()
                    page.get_by_role("button", name="Continuar", exact=True).click()
                    expect(page.get_by_text("🎧 Tocando Agora", exact=True)).to_be_visible()
                    checks.append("Cadastro/login real com conta temporária")
                    page.get_by_text("📁 Importar Áudios", exact=True).click()
                    page.get_by_role("tab", name="🔗 Link de Plataforma").click()
                    for link, title in (
                        ("https://open.spotify.com/track/123", "Spotify marker"),
                        ("https://example.org/music/456", "Generic marker"),
                    ):
                        page.get_by_label("URL HTTPS da música", exact=True).fill(link)
                        page.get_by_label("Título da música (obrigatório)", exact=True).fill(title)
                        page.get_by_role("button", name="🔗 Adicionar Link", exact=True).click()
                        expect(page.get_by_text("Link adicionado à biblioteca!", exact=True)).to_be_visible()
                    checks.append("Cadastro de dois links pela UI")
                    page.get_by_role("tab", name="🎵 Selecionar Arquivos de áudio (Explorador)").click()
                    page.locator('input[type="file"]').set_input_files(media)
                    page.get_by_role("button", name=re.compile("Processar e Importar")).click()
                    expect(page.get_by_text("Total de Faixas:", exact=False)).to_contain_text("5")
                    storage = next((root / "private" / "users").iterdir())
                    stored = json.loads((storage / "library.json").read_text(encoding="utf-8"))
                    assert len(stored) == 5 and sum(t["source_type"] == "external" for t in stored) == 2
                    checks.append("Uploads reais MP3/WAV/FLAC após links preservam todos os registros")
                    page.get_by_text("🎵 Playlists", exact=True).click()
                    page.get_by_role("textbox", name="Nome da Nova Playlist:").fill("Browser mixed")
                    page.get_by_role("button", name="➕ Criar Playlist", exact=True).click()
                    expect(page.get_by_role("heading", name=re.compile("Playlist:.*Browser mixed"))).to_be_visible()
                    page.get_by_text("📚 Biblioteca de Mídias", exact=True).click()
                    expect(page.get_by_role("button", name="+ Playlist", exact=True)).to_have_count(5)
                    for index, track in enumerate(stored):
                        page.locator(f".st-key-add_pl_{track['id']} button").click()
                        # Confirmar o efeito novo, não um toast remanescente do clique anterior.
                        deadline = time.monotonic() + 10
                        while time.monotonic() < deadline:
                            current = json.loads((storage / "playlists.json").read_text(encoding="utf-8"))
                            if len(current[0]["track_ids"]) == index + 1:
                                break
                            time.sleep(.05)
                        else:
                            raise AssertionError("Adição à playlist não foi persistida")
                        expect(page.get_by_test_id("stApp")).to_have_attribute(
                            "data-test-script-state", "notRunning"
                        )
                    page.get_by_text("🎵 Playlists", exact=True).click()
                    expect(page.get_by_role("button", name="❌ Remover", exact=True)).to_have_count(5)
                    page.reload()
                    page.get_by_label("Usuário", exact=True).fill("mixed_browser")
                    page.get_by_label("Senha", exact=True).fill("temporary-browser-test-password")
                    page.get_by_role("button", name="Continuar", exact=True).click()
                    page.get_by_text("🎵 Playlists", exact=True).click()
                    expect(page.get_by_role("button", name="❌ Remover", exact=True)).to_have_count(5)
                    checks.append("Playlist mista criada e preservada após recarga")
                    page.get_by_text("📚 Biblioteca de Mídias", exact=True).click()
                    page.get_by_role("button", name="✏️ Editar", exact=True).first.click()
                    page.get_by_role("textbox", name="Título", exact=True).fill("Edited marker")
                    page.get_by_role("button", name="Salvar Alterações", exact=True).click()
                    expect(page.get_by_text("Edited marker", exact=True).first).to_be_visible()
                    expect(page.get_by_test_id("stApp")).to_have_attribute(
                        "data-test-script-state", "notRunning"
                    )
                    expect(page.get_by_role("link", name="Abrir no serviço", exact=True)).to_have_count(2)
                    checks.append("Edição de metadados externos")
                    # Interceptar navegação externa: verificar a aba sem depender do serviço.
                    page.context.route("https://open.spotify.com/**",
                                       lambda route: route.fulfill(body="External service test"))
                    with page.expect_popup() as popup:
                        page.locator('a[href="https://open.spotify.com/track/123"]').first.click()
                    popup_page = popup.value
                    popup_page.wait_for_load_state()
                    assert popup_page.url == "https://open.spotify.com/track/123"
                    popup_page.close()
                    checks.append("Abertura de serviço em aba cliente (destino interceptado)")
                    page.get_by_role("button", name="▶ Reproduzir Áudios Locais da Biblioteca", exact=True).click()
                    expect(page.get_by_text("2 link(s) excluído(s)", exact=False)).to_be_visible()
                    frame = page.frame_locator('iframe[src*="media_play_browser"]')
                    audio = frame.locator("audio")
                    expect(audio).to_be_visible()
                    audio.evaluate("(audio) => audio.play()")
                    audio.evaluate("""async (audio) => {
                        for(let i=0;i<100 && audio.currentTime<.1;i++)
                            await new Promise(r=>setTimeout(r,50));
                        if(audio.currentTime<.1 || audio.error) throw new Error('Audio did not advance');
                    }""")
                    checks.append("Áudio local reproduz no componente web do colega")
                    page.get_by_text("🎵 Playlists", exact=True).click()
                    expect(page.get_by_role("button", name="❌ Remover", exact=True)).to_have_count(5)
                    # Regra por origem seleciona links sem enviá-los ao áudio.
                    page.get_by_text("Criar playlist inteligente", exact=True).click()
                    name = page.get_by_label("Nome da playlist inteligente", exact=True)
                    name.fill("External smart")
                    name.press("Enter")
                    expect(page.get_by_test_id("stApp")).to_have_attribute(
                        "data-test-script-state", "notRunning"
                    )
                    choose_rule_option(page, "smart_new_rule_0_field", "Origem")
                    choose_rule_option(page, "smart_new_rule_0_source_type_value", "Link externo")
                    page.get_by_role("button", name="Salvar playlist inteligente", exact=True).click()
                    expect(page.get_by_text("2 faixa(s) correspondem às regras.", exact=True)).to_be_visible()
                    before = audio.evaluate("(audio) => ({src:audio.src,time:audio.currentTime})")
                    page.get_by_role("button", name="Reproduzir seleção inteligente", exact=True).click()
                    expect(page.get_by_text("Não há faixas locais nesta seleção.", exact=False)).to_be_visible()
                    assert audio.evaluate("(audio) => audio.src") == before["src"]
                    assert audio.evaluate("(audio) => audio.currentTime") >= before["time"]
                    checks.append("Playlist inteligente por origem preserva reprodução ao conter só links")
                    page.screenshot(path=str(ARTIFACTS / "mixed-playlist.png"), full_page=True)
                    page.get_by_role("button", name="❌ Remover", exact=True).first.click()
                    expect(page.get_by_role("button", name="❌ Remover", exact=True)).to_have_count(4)
                    stored = json.loads((storage / "library.json").read_text(encoding="utf-8"))
                    playlists = json.loads((storage / "playlists.json").read_text(encoding="utf-8"))
                    assert len(stored) == 5 and len(playlists[0]["track_ids"]) == 4
                    assert any(track["title"] == "Edited marker" for track in stored)
                    # Outra conta começa vazia; o primeiro usuário continua intacto.
                    visitor = browser.new_context()
                    second = visitor.new_page()
                    second.goto(url)
                    second.get_by_label("Usuário", exact=True).fill("second_browser")
                    second.get_by_label("Senha", exact=True).fill("temporary-browser-test-password")
                    second.get_by_text("Criar conta", exact=True).click()
                    second.get_by_role("button", name="Continuar", exact=True).click()
                    second.get_by_text("📚 Biblioteca de Mídias", exact=True).click()
                    expect(second.get_by_text("Nenhuma música encontrada na biblioteca.", exact=True)).to_be_visible()
                    assert len(json.loads((storage / "library.json").read_text(encoding="utf-8"))) == 5
                    visitor.close()
                    checks.append("Segunda conta não acessa links, músicas ou playlists da primeira")
                    assert not errors, errors
                    checks.append("Remoção da playlist não exclui registro da biblioteca; sem pageerrors")
                    browser.close()
            finally:
                server.terminate()
                server.wait(timeout=20)
    report = {"checks": checks, "page_errors": errors,
              "limitations": ["Áudio de teste silencioso; Pygame físico desativado",
                              "Serviço externo interceptado; disponibilidade não verificada"]}
    (ARTIFACTS / "result.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=True, indent=2))
    print(f"Artifacts: {ARTIFACTS}")


if __name__ == "__main__":
    main()
