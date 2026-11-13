"""End-to-end browser validation against a temporary, isolated Streamlit server."""

import io
import math
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import soundfile as sf
from playwright.sync_api import sync_playwright, expect
from core.user_storage import register, select_user, reset_user
from core.library import import_uploaded_files


def run():
    with tempfile.TemporaryDirectory() as directory:
        os.environ['MEDIA_PLAY_DATA'] = directory
        register('browser_test', 'temporary-test-password')
        token = select_user('browser_test')
        try:
            uploads = []
            for extension in ('wav', 'flac', 'mp3'):
                content = io.BytesIO()
                sf.write(content, [0.1 * math.sin(2 * math.pi * 440 * i / 16000) for i in range(16000 * 8)], 16000, format=extension.upper())
                content.name = 'test.' + extension
                uploads.append(content)
            import_uploaded_files(uploads)
        finally:
            reset_user(token)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        url = f'http://127.0.0.1:{port}'
        log = open(Path(directory) / 'server.log', 'w', encoding='utf-8')
        process = subprocess.Popen([sys.executable, '-m', 'streamlit', 'run', 'app.py', '--server.headless=true', f'--server.port={port}', '--browser.gatherUsageStats=false'], stdout=log, stderr=log)
        try:
            for _ in range(100):
                try:
                    urllib.request.urlopen(url + '/_stcore/health', timeout=1)
                    break
                except OSError:
                    time.sleep(.2)
            with sync_playwright() as pw:
                options = {'headless': True, 'args': ['--autoplay-policy=no-user-gesture-required']}
                executable = os.environ.get('BROWSER_EXECUTABLE')
                if executable:
                    options['executable_path'] = executable
                browser = pw.chromium.launch(**options)
                page = browser.new_page()
                page.goto(url)
                page.get_by_label('Usuário', exact=True).fill('browser_test')
                page.get_by_label('Senha', exact=True).fill('temporary-test-password')
                page.get_by_role('button', name='Continuar', exact=True).click()
                page.get_by_text('📚 Biblioteca de Mídias', exact=True).click()
                page.get_by_label('Ordenar por', exact=True).click()
                page.get_by_role('option', name='Formato', exact=True).click()
                page.get_by_role('button', name='▶ Reproduzir Toda a Biblioteca na Fila').click()
                # Locate by component URL rather than depending on Streamlit's name prefix.
                frame = page.frame_locator('iframe[src*="media_play_browser"]')
                audio = frame.locator('audio')
                expect(audio).to_be_visible()
                for index in range(3):
                    expected_mime = ('flac', 'mpeg', 'wav')[index]
                    assert audio.evaluate('(a) => a.src').startswith('data:audio/' + expected_mime)
                    audio.evaluate('''async (a) => {
                        for(let i=0;i<100 && a.readyState<1;i++) await new Promise(r=>setTimeout(r,50));
                        if(a.readyState<1) throw new Error('Metadata did not load');
                    }''')
                    audio.evaluate('(a) => a.play()')
                    audio.evaluate('''async (a) => {
                        for(let i=0;i<100 && (a.paused || a.currentTime<.1);i++) await new Promise(r=>setTimeout(r,50));
                        if(a.paused || a.currentTime<.1) throw new Error(JSON.stringify({paused:a.paused,time:a.currentTime,ready:a.readyState,error:a.error?.message}));
                    }''')
                    assert audio.evaluate('(a) => a.error === null'), 'Codec failure'
                    audio.evaluate('(a) => a.pause()')
                    position = audio.evaluate('(a) => a.currentTime')
                    page.wait_for_timeout(350)
                    assert abs(audio.evaluate('(a) => a.currentTime') - position) < .1, 'Pause did not freeze media clock'
                    audio.evaluate('(a) => {a.currentTime=2;}')
                    page.wait_for_timeout(150)
                    assert abs(audio.evaluate('(a) => a.currentTime') - 2) < .3
                    if index < 2:
                        frame.get_by_role('button', name='Próxima', exact=True).click()
                        page.wait_for_timeout(350)
                frame.get_by_role('button', name='Parar', exact=True).click()
                page.wait_for_timeout(250)
                assert audio.evaluate('(a) => a.paused && a.currentTime < .1')
                frame.get_by_role('button', name='Anterior', exact=True).click()
                page.wait_for_timeout(300)
                assert audio.evaluate('(a) => a.src.startsWith("data:audio/mpeg")')
                # Actual ended events, rather than a server timer, advance the queue.
                audio.evaluate('(a) => {a.currentTime=a.duration-.15; a.play();}')
                page.wait_for_timeout(800)
                assert audio.evaluate('(a) => a.src.startsWith("data:audio/wav")')
                frame.get_by_label('Repetir').select_option('one')
                audio.evaluate('(a) => {a.currentTime=a.duration-.15; a.play();}')
                page.wait_for_timeout(800)
                assert audio.evaluate('(a) => a.currentTime < 2 && !a.paused')
                # Streamlit rerenders unrelated widgets without restarting the audio element.
                page.get_by_text('Somente favoritas', exact=True).click()
                page.wait_for_timeout(400)
                assert audio.evaluate('(a) => !a.paused && a.currentTime > .3')
                frame.get_by_label('Repetir').select_option('all')
                audio.evaluate('(a) => {a.currentTime=a.duration-.15; a.play();}')
                page.wait_for_timeout(700)
                assert audio.evaluate('(a) => a.src.startsWith("data:audio/flac")')
                source = audio.evaluate('(a) => a.src')
                frame.get_by_role('button', name='Aleatório', exact=True).click()
                expect(frame.get_by_role('button', name='Aleatório', exact=True)).to_have_attribute('aria-pressed', 'true')
                assert audio.evaluate('(a) => a.src') == source
                frame.get_by_role('button', name='Próxima', exact=True).click()
                page.wait_for_timeout(250)
                assert audio.evaluate('(a) => a.src') != source
                Path('artifacts').mkdir(exist_ok=True)
                page.screenshot(path='artifacts/browser-library.png', full_page=True)
                assert page.get_by_test_id('stException').count() == 0
                # A separate browser context cannot see the authenticated library.
                visitor = browser.new_context()
                second = visitor.new_page()
                second.goto(url)
                expect(second.get_by_role('button', name='Continuar', exact=True)).to_be_visible()
                expect(second.get_by_role('button', name='Favoritar', exact=True)).to_have_count(0)
                visitor.close()
                browser.close()
            print('PASS: browser decoded WAV/FLAC/MP3; play, pause, seek, next, stop and anonymous isolation')
        finally:
            process.terminate()
            process.wait(timeout=15)
            log.close()


if __name__ == '__main__':
    run()
