"""Use real media time to prove seeks, pauses and rerenders do not inflate history."""

from playwright.sync_api import expect
from pathlib import Path


def check_history(page, frame, audio):
    audio.evaluate('''async a => {
        for(let i=0;i<100 && (command<1 || a.readyState<1);i++) await new Promise(r=>setTimeout(r,50));
        if(a.readyState<1) throw new Error('History fixture did not load');
        a.pause();
    }''')
    page.get_by_text('📊 Histórico', exact=True).click()
    metric = page.get_by_test_id('stMetric').filter(has_text='Reproduções confirmadas').get_by_test_id('stMetricValue')
    expect(metric).to_have_text('0')
    # Seeking changes media position, not elapsed listening time.
    audio.evaluate('a=>{a.currentTime=10;}')
    audio.evaluate('a=>a.play()')
    page.wait_for_timeout(1700)
    audio.evaluate('a=>a.pause()')
    expect(metric).to_have_text('0')
    page.wait_for_timeout(1200)
    expect(metric).to_have_text('0')
    audio.evaluate('a=>{a.currentTime=20;}')
    audio.evaluate('a=>a.play()')
    page.wait_for_timeout(1500)
    audio.evaluate('a=>a.pause()')
    expect(metric).to_have_text('0')
    audio.evaluate('a=>a.play()')
    expect(metric).to_have_text('1', timeout=12000)
    audio.evaluate('a=>a.pause()')
    page.get_by_label('Período do histórico', exact=True).click()
    page.keyboard.press('Home')
    page.keyboard.press('Enter')
    expect(metric).to_have_text('1')
    audio.evaluate('a=>{a.currentTime=1;}')
    audio.evaluate('a=>a.play()')
    page.wait_for_timeout(1000)
    audio.evaluate('a=>a.pause()')
    expect(metric).to_have_text('1')
    page.get_by_role('button', name='Adicionar ao final da fila', exact=True).click()
    expect(metric).to_have_text('1')
    page.get_by_role('button', name='Tocar novamente', exact=True).click()
    expect(metric).to_have_text('2', timeout=12000)
    audio.evaluate('a=>a.pause()')
    Path('artifacts').mkdir(exist_ok=True)
    page.get_by_role('heading', name='Histórico e estatísticas', exact=True).scroll_into_view_if_needed()
    page.screenshot(path='artifacts/listening-history.png', full_page=True)
    page.get_by_text('Limpar meu histórico', exact=True).click()
    page.get_by_text('Confirmo a limpeza de todo o meu histórico', exact=True).click()
    page.get_by_role('button', name='Limpar histórico', exact=True).click()
    expect(metric).to_have_text('0')
    audio.evaluate('a=>a.play()')
    page.wait_for_timeout(1100)
    audio.evaluate('a=>a.pause()')
    expect(metric).to_have_text('0')
    # Restore the full collection for queue and codec regression checks.
    page.get_by_text('📚 Biblioteca de Mídias', exact=True).click()
    command_before = audio.evaluate('()=>command')
    page.get_by_role('button', name='▶ Reproduzir Áudios Locais da Biblioteca', exact=True).click()
    audio.evaluate('''async (a, before) => {
        for(let i=0;i<100 && (command<=before || a.readyState<1);i++) await new Promise(r=>setTimeout(r,50));
        if(command<=before) throw new Error('History regression did not restore queue');
    }''', command_before)
