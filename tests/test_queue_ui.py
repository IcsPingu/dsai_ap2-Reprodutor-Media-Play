import unittest
from streamlit.testing.v1 import AppTest


SCRIPT = '''
import streamlit as st
from core.player import AudioPlayer
from ui.queue_editor import render_queue_editor, render_enqueue_actions
if "player" not in st.session_state:
    player = AudioPlayer(browser=True)
    player.set_queue([dict(id=x, title=x, duration=60) for x in ("a", "b", "c")])
    st.session_state.player = player
player = st.session_state.player
render_enqueue_actions(player, dict(id="d", title="d", duration=30))
render_queue_editor(player)
'''


class QueueUITests(unittest.TestCase):
    def setUp(self):
        self.app = AppTest.from_string(SCRIPT).run()

    def click(self, label, index=0):
        buttons = [button for button in self.app.button if button.label == label]
        buttons[index].click().run()
        self.assertEqual(len(self.app.exception), 0)

    def ids(self):
        return [t["id"] for t in self.app.session_state.player.queue]

    def test_enqueue_next_and_end_controls(self):
        self.click("Tocar depois")
        self.assertEqual(self.ids(), ["a", "d", "b", "c"])
        self.click("Adicionar ao final")
        self.assertEqual(self.ids(), ["a", "d", "b", "c", "d"])

    def test_move_remove_and_clear_controls(self):
        self.click("Descer", 1)
        self.assertEqual(self.ids(), ["a", "c", "b"])
        self.click("Subir", 2)
        self.assertEqual(self.ids(), ["a", "b", "c"])
        self.click("Remover da fila", 1)
        self.assertEqual(self.ids(), ["a", "c"])
        self.click("Limpar próximas")
        self.assertEqual(self.ids(), ["a"])
        self.assertTrue(next(b for b in self.app.button if b.label == "Limpar próximas").disabled)

    def test_current_controls_disabled_and_duration_visible(self):
        for label in ("Subir", "Descer", "Remover da fila"):
            self.assertTrue(next(b for b in self.app.button if b.label == label).disabled)
        self.assertTrue(any("02:00" in text.value for text in self.app.caption))


if __name__ == "__main__":
    unittest.main()
