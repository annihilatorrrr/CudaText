import os
import cudatext as app
from cudatext import *
from cudax_lib import get_translation
from .lexertypes import *

_   = get_translation(__file__)  # I18N

config_file = os.path.join(app_path(APP_DIR_SETTINGS), 'plugins.ini')
config_section = 'lexer_detecter_ignore'

def log(*args):
    pass
    #print(*args)

def get_zip_filenames(filename):
    from zipfile import ZipFile
    res = []
    with ZipFile(filename, 'r') as z:
        res = z.namelist()
    res.remove('install.inf')
    return res


class Command:

    def on_open_none(self, ed_self):

        fn = ed_self.get_filename()
        if not fn:
            return

        name = os.path.basename(fn)
        ext1 = ''
        ext2 = ''

        if '.' in name:
            ext1 = name[name.rfind('.')+1:]
            s = name[:name.rfind('.'):]
            if '.' in s:
                ext2 = s[s.rfind('.')+1:] + '.' + ext1

        if ext1:
            if ini_read(config_file, config_section, ext1, '')=='1':
                return

        log('Lexer detecter: name, ext1, ext2:', name, ext1, ext2)
        lexers = []

        log('Lexer detecter: search by name:', '/'+name)
        lex = TYPES.get('/'+name, '')
        if lex:
            lexers += lex

        if os.name=='nt':
            ext1b = ext1.lower()
            ext2b = ext2.lower()
        else:
            ext1b = ext1
            ext2b = ext2

        if ext2:
            log('Lexer detecter: search by ext2:', ext2)
            lex = TYPES.get(ext2, '')
            if not lex and ext2b != ext2:
                lex = TYPES.get(ext2b, '')
            if lex:
                lexers += lex

        if ext1:
            log('Lexer detecter: search by ext1:', ext1)
            lex = TYPES.get(ext1, '')
            if not lex and ext1b != ext1:
                lex = TYPES.get(ext1b, '')
            if lex:
                lexers += lex

        if not lexers:
            return

        items = [_('Download lexer: ')+s for s in lexers]
        items += [_('Cancel')]
        add_ignore = bool(ext1)
        if add_ignore:
            items += [_('Cancel, don\'t suggest anymore for *.%s') % ext1]

        res = dlg_menu(DMENU_LIST, items, caption=_('Lexer(s) for "%s"') % name)
        if res is None:
            return

        if add_ignore:
            if res == len(items)-2:
                return
            if res == len(items)-1:
                ini_write(config_file, config_section, ext1, '1')
                return
        else:
            if res == len(items)-1:
                return

        lex = lexers[res]
        log('Detected lexer:', lex)

        # imports are here to speedup plugin load when no lexers found
        import json
        import tempfile
        from urllib.parse import quote
        from cuda_addonman import opt
        from cuda_addonman.work_remote import get_url

        url_filename = 'lexer.' + lex.replace(' ', '_') + '.zip'
        url = 'https://sourceforge.net/projects/cudatext/files/addons/lexers/' + quote(url_filename)

        tempdir = tempfile.gettempdir()+os.sep+'cudatext'
        if not os.path.isdir(tempdir):
            os.mkdir(tempdir)
        tempname = tempdir+os.sep+'lexer.zip'
        get_url(url, tempname, True)
        if not os.path.isfile(tempname):
            msg_box(_('Could not download/install lexer "%s" from add-ons') % lex, MB_OK+MB_ICONERROR)
            return

        file_open(tempname, options='/silent')
        lexer_proc(LEXER_REREAD_LIB, '')

        if lexer_proc(LEXER_GET_PROP, lex) is not None:
            ed_self.set_prop(PROP_LEXER_FILE, lex)
        elif lexer_proc(LEXER_GET_PROP, lex+' ^') is not None:
            ed_self.set_prop(PROP_LEXER_FILE, lex+' ^')
        else:
            print('NOTE: Cannot activate just installed lexer "%s"' % lex)


        def get_lexer_version(section):
            urls = [url for url in opt.ch_def if url.endswith('/lexers.json')]
            if not urls:
                return ''
            lexers_url = urls[0]
            lexers_json = tempdir + os.sep + 'lexers.json'
            get_url(lexers_url, lexers_json, True)
            lexers_json_data = json.loads(open(lexers_json).read())
            for i_ in lexers_json_data:
                for k_, v_ in i_.items():
                    if k_ == 'url' and section in v_:
                        return i_['v']

        fn_pkg = os.path.join(app_path(APP_DIR_SETTINGS), 'packages.ini')
        section = url_filename
        version = get_lexer_version(section) or '' # avoid None value
        ini_write(fn_pkg, section, 'd', 'data/lexlib')
        ini_write(fn_pkg, section, 'f', ';'.join(get_zip_filenames(tempname)))
        ini_write(fn_pkg, section, 'v', version)
        print(_('Installed lexer "%s", version "%s"')%(lex, version))
