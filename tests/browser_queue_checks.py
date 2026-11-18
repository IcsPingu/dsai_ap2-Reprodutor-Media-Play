"""Exercise edits against a real HTMLAudioElement, including paused continuity."""

from playwright.sync_api import expect


def wait_queue_update(audio, previous):
    audio.evaluate('''async (a, previous) => {
        for(let i=0;i<100 && queueVersion<=previous;i++) await new Promise(r=>setTimeout(r,50));
        if(queueVersion<=previous) throw new Error('Queue revision was not delivered');
    }''', previous)


def check_queue_edits(page, frame, audio):
    audio.evaluate('''async a => {
        for(let i=0;i<100 && (command<1 || tracks.length!==3 || a.readyState<1);i++) await new Promise(r=>setTimeout(r,50));
        if(command<1 || tracks.length!==3 || a.readyState<1) throw new Error('Initial queue did not load');
        await a.play();
        a.currentTime=1;
        a.__queueProbe='preserved';
        a.__queueLoads=0;
        a.addEventListener('loadstart',()=>a.__queueLoads++);
    }''')
    page.wait_for_timeout(200)
    position = audio.evaluate('a=>a.currentTime')
    version = audio.evaluate('()=>queueVersion')
    page.get_by_role('button', name='Adicionar à fila', exact=True).first.click()
    page.get_by_role('button', name='Tocar depois', exact=True).click()
    wait_queue_update(audio, version)
    assert audio.evaluate('a=>a.__queueProbe') == 'preserved'
    assert audio.evaluate('a=>a.__queueLoads') == 0, 'Enqueue reloaded current media'
    assert audio.evaluate('a=>!a.paused && a.currentTime>=0')
    assert audio.evaluate('a=>a.currentTime') >= position
    page.keyboard.press('Escape')
    page.get_by_text('🎧 Tocando Agora', exact=True).click()
    page.wait_for_timeout(250)
    assert audio.evaluate('a=>a.__queueProbe') == 'preserved', 'Navigation recreated audio element'
    version = audio.evaluate('()=>queueVersion')
    page.get_by_role('button', name='Descer', exact=True).nth(1).click()
    wait_queue_update(audio, version)
    assert audio.evaluate('a=>a.__queueLoads') == 0, 'Move reloaded current media'
    version = audio.evaluate('()=>queueVersion')
    page.get_by_role('button', name='Remover da fila', exact=True).nth(1).click()
    wait_queue_update(audio, version)
    assert audio.evaluate('a=>a.__queueLoads') == 0, 'Remove reloaded current media'
    version = audio.evaluate('()=>queueVersion')
    page.get_by_role('button', name='Limpar próximas', exact=True).click()
    wait_queue_update(audio, version)
    assert audio.evaluate('a=>a.__queueLoads') == 0, 'Clear reloaded current media'
    expect(page.get_by_role('button', name='Remover da fila', exact=True)).to_have_count(1)
    audio.evaluate('a=>a.pause()')
    page.wait_for_timeout(150)
    paused_position = audio.evaluate('a=>a.currentTime')
    page.get_by_text('📚 Biblioteca de Mídias', exact=True).click()
    assert audio.evaluate('a=>a.__queueProbe') == 'preserved', 'Returning to library remounted the player'
    version = audio.evaluate('()=>queueVersion')
    page.get_by_role('button', name='Adicionar à fila', exact=True).first.click()
    page.get_by_role('button', name='Adicionar ao final', exact=True).click()
    wait_queue_update(audio, version)
    assert audio.evaluate('a=>a.paused'), 'Editing resumed paused audio'
    assert abs(audio.evaluate('a=>a.currentTime') - paused_position) < .1
    assert audio.evaluate('a=>a.__queueLoads') == 0, 'Audio component was remounted or source was reloaded'
    page.keyboard.press('Escape')
    # Restore a predictable queue for the codec/transport regression tests.
    version = audio.evaluate('()=>queueVersion')
    page.get_by_role('button', name='▶ Reproduzir Áudios Locais da Biblioteca').click()
    wait_queue_update(audio, version)
