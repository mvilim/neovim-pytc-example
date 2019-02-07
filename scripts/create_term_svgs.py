# requires pynput and termtosvg
# additionally, requires a patched version of pyte, see https://github.com/selectel/pyte/pull/103

# TODO: it would probably be better to use a fake source of terminal input and pipe it directly to the editor (so that
# this SVG generation can be run in the background)

from threading import Thread
from time import sleep
import warnings
from pynput.keyboard import Key, Controller
import os


lorem_ipsum_text = '''Lorem ipsum dolor sit amet, at adipiscing dissentiet eam, utinam aperiri invidunt in sea, ius persius suscipiantur et. Per ut omnesque molestie, et audire vocibus repudiandae sed. No vel facer offendit conceptam, ad vel solum expetendis, tota vivendo sit in. Quo et zril latine indoctum, et sed paulo putent appellantur.

Vel fabulas laoreet id, at quo discere albucius invenire. Ea dolores recusabo reformidans mel. Mucius scripta molestie ex nam. Nam cu bonorum quaestio cotidieque, eu cum delenit appareat inciderint, an soluta conceptam pri.

Erant laudem philosophia ei vim. Vix lorem efficiantur ut, cibo graecis propriae in duo, mollis civibus ullamcorper an mei. Eu eam prima mollis habemus, at nostro offendit intellegebat mei, graecis voluptatibus mediocritatem in has. Ei prompta accusam his. In eum copiosae inciderint, dolor habemus propriae cu vix. Cu usu summo salutatus.

Nostro denique accommodare nam an. Eam eius laboramus scribentur ex, ad falli choro impedit mea. Equidem democritum vix an. Pro ne probo euripidis, sit te malis repudiandae. Id pro deseruisse neglegentur, no brute posse dignissim eam.

Mundi adipiscing cu duo, exerci graeco commodo ad mel, ei sumo impetus intellegam nam. Mea homero dissentiet id. Fugit erant reformidans ex pri, utinam audiam docendi ad usu, in tale possim pertinax vis. Eu quo dicit mandamus percipitur, inermis pertinacia forensibus ei duo. Nonumy quodsi appareat usu cu, cu vix error utinam patrioque, no vel dicunt partiendo accommodare.
'''

editor_commands = ['nvim', 'neovim_pytc']
term_to_svg = 'termtosvg'


class InputThread(Thread):
    def __init__(self, cps=500):
        super(InputThread, self).__init__()
        self.c = Controller()
        self.cps = cps

    def tap(self, key):
        self.c.press(key)
        self.c.release(key)

    def type(self, text, cps=None):
        if cps is None:
            cps = self.cps
        for c in text:
            key = self.c._CONTROL_CODES.get(c, c)
            self.tap(key)
            sleep(1 / cps)

    def run(self):
        sleep(1)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=DeprecationWarning)
            # add some text
            # enter insert mode
            self.tap('i')
            # write lorem ipsum text
            self.type(lorem_ipsum_text, 500)
            # return to normal node
            self.tap(Key.esc)

            # return to the top of the file
            self.type('k' * lorem_ipsum_text.count('\n'), cps=8)
            sleep(1)

            # add a header
            self.type('O')
            sleep(0.5)
            self.type('# Lorem Ipsum', cps=50)
            sleep(0.5)
            self.tap(Key.esc)
            sleep(0.5)

            # fold the text
            self.type('Go', cps=4)
            self.tap(Key.esc)
            sleep(0.25)
            self.type('zM')
            sleep(2)

            # unfold the text
            self.type('zR')
            sleep(2)

            # display the help
            self.tap(Key.f1)
            sleep(2)
            self.type(':q')
            self.tap(Key.enter)
            sleep(2)

            # exit the editor
            self.type(':q!')
            self.tap(Key.enter)


for editor in editor_commands:
    InputThread().start()
    os.system('termtosvg -c \'{} test.md\' {}_capture.svg'.format(editor, editor))
