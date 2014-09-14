import vim
import re
import tempfile
import utils

from geeknote.geeknote import *
from geeknote.tools    import *
from geeknote.editor   import Editor

explorer = None

#======================== Vimscript Entry-points =============================#

def vim_geeknote_activate_node():
    global explorer

    current_line = vim.current.line

    r = re.compile('N.+ \[(.+)\]$')
    m = r.match(current_line)
    if m:
        guid = m.group(1)
        explorer.toggle(guid)

        row, col = vim.current.window.cursor
        explorer.render()
        vim.current.window.cursor = (row, col)

    r = re.compile('\s+n.+ \[(.+)\]$')
    m = r.match(current_line)
    if m:
        guid = m.group(1)
        note = GeekNote().getNote(guid)
        GeekNoteShowNote(note)
        return

def vim_geeknote_toggle():
    global explorer

    notebooks_buffer = 't:vim_geeknote_notebooks'
    utils.vsplit(notebooks_buffer, 50)
    explorer = Explorer()

    notebooks = GeekNote().findNotebooks()
    for notebook in notebooks:
        explorer.add(notebook)
    explorer.render()
    vim.current.window.cursor = (1, 0)

#======================== Classes ============================================#

class Explorer(object):
    nodes = []

    def add(self, notebook):
        notes = GeeknoteGetNotes(notebook)
        node  = {'notebook':notebook, 'notes':notes, 'expand':False}
        self.nodes.append(node)

    def expandAll(self):
        for node in self.nodes:
            node['expand'] = True

    def toggle(self, guid):
        target = None

        for node in self.nodes:
            notebook = node['notebook']
            if notebook.guid == guid:
                target = node
                break

        if target:
            target['expand'] = not target['expand']

    def render(self):
        vim.command('setlocal modifiable')
        vim.command('normal! ggdG')

        content = []
        content.append("Notebooks:")
        content.append("{:=^50}".format("="))

        for node in self.nodes:
            notebook = node['notebook']
            notes    = node['notes']

            total = len(notes)
            line  = "N {0} ({1})".format(notebook.name, str(total))
            content.append('{:<46} [{}]'.format(line, notebook.guid))

            if node['expand']:
                for note in notes:
                    name = ""
                    if hasattr(note, 'title'):
                        name = note.title
                    elif hasattr(note, 'name'):
                        name = notes.name

                    name = (name[:38] + '..') if len(name) > 40 else name
                    line = "    n {:<40} [{}]".format(name, note.guid)
                    content.append(line)

        vim.command('call append(0, {})'.format(content))
        vim.command('setlocal nomodifiable')

#======================== Geeknote Helper Functions  =========================#

def GeeknoteGetNotes(notebook):
    notes = []
    results = Notes().get(None, None, notebook.name)
    total = len(results.notes)
    for key, note in enumerate(results.notes):
        notes.append(note)
    return notes

def GeekNoteShowNote(note):
    prevWin        = utils.winnr('#')
    isPrevUsable   = utils.isWindowUsable(prevWin)
    firstUsableWin = utils.firstUsableWindow()

    if (isPrevUsable is False) and (firstUsableWin == -1):
        vim.command("exec {} . \"wincmd p\"".format(prevWin))
        vim.command('vertical new')
    else:
        if isPrevUsable is False:
            vim.command("exec {} . \"wincmd w\"".format(firstUsableWin))
        else:
            vim.command("exec \"wincmd p\"")

    text = Editor.ENMLtoText(note.content)
    text = text + "\n"
    text = tools.stdoutEncode(text)

    f = tempfile.NamedTemporaryFile(delete=False)
    f.write(text)
    f.close()

    vim.command("edit {}".format(f.name))
    prevWin = utils.winnr('#')
    vim.command("exec {} . \"wincmd p\"".format(prevWin))


