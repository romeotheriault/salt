import os
import shutil
import tempfile
import stat
from saltunittest import TestCase, TestLoader, TextTestRunner

import salt.utils.find


class TestFind(TestCase):

    def test_parse_interval(self):
        self.assertRaises(ValueError, salt.utils.find._parse_interval, 'w')
        self.assertRaises(ValueError, salt.utils.find._parse_interval, '1s1w')
        self.assertRaises(ValueError, salt.utils.find._parse_interval, '1s1s')

        result, resolution = salt.utils.find._parse_interval('')
        self.assertEqual(result, 0)
        self.assertIs(resolution, None)

        result, resolution = salt.utils.find._parse_interval('1')
        self.assertEqual(result, 86400.0)
        self.assertEqual(resolution, 86400)

        result, resolution = salt.utils.find._parse_interval('1s')
        self.assertEqual(result, 1.0)
        self.assertEqual(resolution, 1)

        result, resolution = salt.utils.find._parse_interval('1m')
        self.assertEqual(result, 60.0)
        self.assertEqual(resolution, 60)

        result, resolution = salt.utils.find._parse_interval('1h')
        self.assertEqual(result, 3600.0)
        self.assertEqual(resolution, 3600)

        result, resolution = salt.utils.find._parse_interval('1d')
        self.assertEqual(result, 86400.0)
        self.assertEqual(resolution, 86400)

        result, resolution = salt.utils.find._parse_interval('1w')
        self.assertEqual(result, 604800.0)
        self.assertEqual(resolution, 604800)

        result, resolution = salt.utils.find._parse_interval('1w3d6h')
        self.assertEqual(result, 885600.0)
        self.assertEqual(resolution, 3600)

        result, resolution = salt.utils.find._parse_interval('1m1s')
        self.assertEqual(result, 61.0)
        self.assertEqual(resolution, 1)

        result, resolution = salt.utils.find._parse_interval('1m2s')
        self.assertEqual(result, 62.0)
        self.assertEqual(resolution, 1)

    def test_parse_size(self):
        self.assertRaises(ValueError, salt.utils.find._parse_size, '')
        self.assertRaises(ValueError, salt.utils.find._parse_size, '1s1s')
        min_size, max_size = salt.utils.find._parse_size('1')
        self.assertEqual(min_size, 1)
        self.assertEqual(max_size, 1)

        min_size, max_size = salt.utils.find._parse_size('1b')
        self.assertEqual(min_size, 1)
        self.assertEqual(max_size, 1)

        min_size, max_size = salt.utils.find._parse_size('1k')
        self.assertEqual(min_size, 1024)
        self.assertEqual(max_size, 2047)

        min_size, max_size = salt.utils.find._parse_size('1m')
        self.assertEqual(min_size, 1048576)
        self.assertEqual(max_size, 2097151)

        min_size, max_size = salt.utils.find._parse_size('1g')
        self.assertEqual(min_size, 1073741824)
        self.assertEqual(max_size, 2147483647)

        min_size, max_size = salt.utils.find._parse_size('1t')
        self.assertEqual(min_size, 1099511627776)
        self.assertEqual(max_size, 2199023255551)

        min_size, max_size = salt.utils.find._parse_size('0m')
        self.assertEqual(min_size, 0)
        self.assertEqual(max_size, 1048575)

        min_size, max_size = salt.utils.find._parse_size('-1m')
        self.assertEqual(min_size, 0)
        self.assertEqual(max_size, 1048576)

        min_size, max_size = salt.utils.find._parse_size('+1m')
        self.assertEqual(min_size, 1048576)
        self.assertEqual(max_size, 2147483647)

        min_size, max_size = salt.utils.find._parse_size('+1M')
        self.assertEqual(min_size, 1048576)
        self.assertEqual(max_size, 2147483647)

    def test_option_requires(self):
        option = salt.utils.find.Option()
        self.assertEqual(option.requires(), salt.utils.find._REQUIRES_PATH)

    def test_name_option_match(self):
        option = salt.utils.find.NameOption('name', '*.txt')
        self.assertIs(option.match('', '', ''), None)
        self.assertIs(option.match('', 'hello.txt', '').group(), 'hello.txt')
        self.assertIs(option.match('', 'HELLO.TXT', ''), None)

    def test_iname_option_match(self):
        option = salt.utils.find.InameOption('name', '*.txt')
        self.assertIs(option.match('', '', ''), None)
        self.assertIs(option.match('', 'hello.txt', '').group(), 'hello.txt')
        self.assertIs(option.match('', 'HELLO.TXT', '').group(), 'HELLO.TXT')

    def test_regex_option_match(self):
        self.assertRaises(ValueError, salt.utils.find.RegexOption, 'name', '(.*}')

        option = salt.utils.find.RegexOption('name', '.*\.txt')
        self.assertIs(option.match('', '', ''), None)
        self.assertIs(option.match('', 'hello.txt', '').group(), 'hello.txt')
        self.assertIs(option.match('', 'HELLO.TXT', ''), None)

    def test_iregex_option_match(self):
        self.assertRaises(ValueError, salt.utils.find.IregexOption, 'name', '(.*}')

        option = salt.utils.find.IregexOption('name', '.*\.txt')
        self.assertIs(option.match('', '', ''), None)
        self.assertIs(option.match('', 'hello.txt', '').group(), 'hello.txt')
        self.assertIs(option.match('', 'HELLO.TXT', '').group(), 'HELLO.TXT')

    def test_type_option_requires(self):
        self.assertRaises(ValueError, salt.utils.find.TypeOption, 'type', 'w')

        option = salt.utils.find.TypeOption('type', 'd')
        self.assertEqual(option.requires(), salt.utils.find._REQUIRES_STAT)

    def test_type_option_match(self):
        option = salt.utils.find.TypeOption('type', 'b')
        self.assertEqual(option.match('', '', [stat.S_IFREG]), False)

        option = salt.utils.find.TypeOption('type', 'c')
        self.assertEqual(option.match('', '', [stat.S_IFREG]), False)

        option = salt.utils.find.TypeOption('type', 'd')
        self.assertEqual(option.match('', '', [stat.S_IFREG]), False)

        option = salt.utils.find.TypeOption('type', 'f')
        self.assertEqual(option.match('', '', [stat.S_IFREG]), True)

        option = salt.utils.find.TypeOption('type', 'l')
        self.assertEqual(option.match('', '', [stat.S_IFREG]), False)

        option = salt.utils.find.TypeOption('type', 'p')
        self.assertEqual(option.match('', '', [stat.S_IFREG]), False)

        option = salt.utils.find.TypeOption('type', 's')
        self.assertEqual(option.match('', '', [stat.S_IFREG]), False)

        option = salt.utils.find.TypeOption('type', 'b')
        self.assertEqual(option.match('', '', [stat.S_IFBLK]), True)

        option = salt.utils.find.TypeOption('type', 'c')
        self.assertEqual(option.match('', '', [stat.S_IFCHR]), True)

        option = salt.utils.find.TypeOption('type', 'd')
        self.assertEqual(option.match('', '', [stat.S_IFDIR]), True)

        option = salt.utils.find.TypeOption('type', 'l')
        self.assertEqual(option.match('', '', [stat.S_IFLNK]), True)

        option = salt.utils.find.TypeOption('type', 'p')
        self.assertEqual(option.match('', '', [stat.S_IFIFO]), True)

        option = salt.utils.find.TypeOption('type', 's')
        self.assertEqual(option.match('', '', [stat.S_IFSOCK]), True)

    def test_owner_option_requires(self):
        self.assertRaises(ValueError, salt.utils.find.OwnerOption, 'owner', 'notexist')

        option = salt.utils.find.OwnerOption('owner', 'root')
        self.assertEqual(option.requires(), salt.utils.find._REQUIRES_STAT)

    def test_owner_option_match(self):
        option = salt.utils.find.OwnerOption('owner', 'root')
        self.assertEqual(option.match('', '', [0] * 5), True)

        option = salt.utils.find.OwnerOption('owner', '500')
        self.assertEqual(option.match('', '', [500] * 5), True)

    def test_group_option_requires(self):
        self.assertRaises(ValueError, salt.utils.find.GroupOption, 'group', 'notexist')

        option = salt.utils.find.GroupOption('group', 'root')
        self.assertEqual(option.requires(), salt.utils.find._REQUIRES_STAT)

    def test_group_option_match(self):
        option = salt.utils.find.GroupOption('group', 'root')
        self.assertEqual(option.match('', '', [0] * 6), True)

        option = salt.utils.find.GroupOption('group', '500')
        self.assertEqual(option.match('', '', [500] * 6), True)

    def test_size_option_requires(self):
        self.assertRaises(ValueError, salt.utils.find.SizeOption, 'size', '1s1s')

        option = salt.utils.find.SizeOption('size', '+1G')
        self.assertEqual(option.requires(), salt.utils.find._REQUIRES_STAT)

    def test_size_option_match(self):
        option = salt.utils.find.SizeOption('size', '+1k')
        self.assertEqual(option.match('', '', [10000] * 7), True)

        option = salt.utils.find.SizeOption('size', '+1G')
        self.assertEqual(option.match('', '', [10000] * 7), False)

    def test_mtime_option_requires(self):
        self.assertRaises(ValueError, salt.utils.find.MtimeOption, 'mtime', '4g')

        option = salt.utils.find.MtimeOption('mtime', '1d')
        self.assertEqual(option.requires(), salt.utils.find._REQUIRES_STAT)

    def test_mtime_option_match(self):
        option = salt.utils.find.MtimeOption('mtime', '1w')
        self.assertEqual(option.match('', '', [1] * 9), False)

        option = salt.utils.find.MtimeOption('mtime', '1s')
        self.assertEqual(option.match('', '', [10 ** 10] * 9), True)


class TestGrepOption(TestCase):

    def setUp(self):
        super(TestGrepOption, self).setUp()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        super(TestGrepOption, self).tearDown()

    def test_grep_option_requires(self):
        self.assertRaises(ValueError, salt.utils.find.GrepOption, 'grep', '(foo)|(bar}')

        option = salt.utils.find.GrepOption('grep', '(foo)|(bar)')
        self.assertEqual(option.requires(),
            (salt.utils.find._REQUIRES_CONTENTS | salt.utils.find._REQUIRES_STAT))

    def test_grep_option_match_regular_file(self):
        hello_file = os.path.join(self.tmpdir, 'hello.txt')
        fd = open(hello_file, 'w')
        fd.write("foo")
        fd.close()
        option = salt.utils.find.GrepOption('grep', 'foo')
        self.assertEqual(option.match(self.tmpdir, 'hello.txt', os.stat(hello_file)), hello_file)

        option = salt.utils.find.GrepOption('grep', 'bar')
        self.assertEqual(option.match(self.tmpdir, 'hello.txt', os.stat(hello_file)), None)

    def test_grep_option_match_dev_null(self):
        option = salt.utils.find.GrepOption('grep', 'foo')
        self.assertEqual(option.match('dev', 'null', os.stat('/dev/null')), None)


class TestPrintOption(TestCase):

    def setUp(self):
        super(TestPrintOption, self).setUp()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        super(TestPrintOption, self).tearDown()

    def test_print_option_defaults(self):
        option = salt.utils.find.PrintOption('print', '')
        self.assertEqual(option.need_stat, False)
        self.assertEqual(option.print_title, False)
        self.assertEqual(option.fmt, ['path'])

    def test_print_option_requires(self):
        option = salt.utils.find.PrintOption('print', '')
        self.assertEqual(option.requires(), salt.utils.find._REQUIRES_PATH)

        option = salt.utils.find.PrintOption('print', 'name')
        self.assertEqual(option.requires(), salt.utils.find._REQUIRES_PATH)

        option = salt.utils.find.PrintOption('print', 'path')
        self.assertEqual(option.requires(), salt.utils.find._REQUIRES_PATH)

        option = salt.utils.find.PrintOption('print', 'name,path')
        self.assertEqual(option.requires(), salt.utils.find._REQUIRES_PATH)

        option = salt.utils.find.PrintOption('print', 'user')
        self.assertEqual(option.requires(), salt.utils.find._REQUIRES_STAT)

        option = salt.utils.find.PrintOption('print', 'path user')
        self.assertEqual(option.requires(), salt.utils.find._REQUIRES_STAT)

    def test_print_option_execute(self):
        hello_file = os.path.join(self.tmpdir, 'hello.txt')
        fd = open(hello_file, 'w')
        fd.write("foo")
        fd.close()

        option = salt.utils.find.PrintOption('print', '')
        self.assertEqual(option.execute('', [0] * 9), '')

        option = salt.utils.find.PrintOption('print', 'path')
        self.assertEqual(option.execute('test_name', [0] * 9), 'test_name')

        option = salt.utils.find.PrintOption('print', 'name')
        self.assertEqual(option.execute('test_name', [0] * 9), 'test_name')

        option = salt.utils.find.PrintOption('print', 'size')
        self.assertEqual(option.execute(hello_file, os.stat(hello_file)), 3)

        option = salt.utils.find.PrintOption('print', 'type')
        self.assertEqual(option.execute(hello_file, os.stat(hello_file)), 'f')

        option = salt.utils.find.PrintOption('print', 'mode')
        self.assertEqual(option.execute(hello_file, range(10)), 0)

        option = salt.utils.find.PrintOption('print', 'mtime')
        self.assertEqual(option.execute(hello_file, range(10)), 8)

        option = salt.utils.find.PrintOption('print', 'user')
        self.assertEqual(option.execute('', [0] * 10), 'root')

        option = salt.utils.find.PrintOption('print', 'user')
        self.assertEqual(option.execute('', [2 ** 31] * 10), 2 ** 31)

        option = salt.utils.find.PrintOption('print', 'group')
        self.assertEqual(option.execute('', [0] * 10), 'root')

        option = salt.utils.find.PrintOption('print', 'group')
        self.assertEqual(option.execute('', [2 ** 31] * 10), 2 ** 31)

        option = salt.utils.find.PrintOption('print', 'md5')
        self.assertEqual(option.execute(hello_file, os.stat(hello_file)),
            'acbd18db4cc2f85cedef654fccc4a4d8')

        option = salt.utils.find.PrintOption('print', 'md5')
        self.assertEqual(option.execute('/dev/null', os.stat('/dev/null')), '')

        option = salt.utils.find.PrintOption('print', 'path name')
        self.assertEqual(option.execute('test_name', [0] * 9),
            ['test_name', 'test_name'])

        option = salt.utils.find.PrintOption('print', 'size name')
        self.assertEqual(option.execute('test_name', [0] * 9),
            [0, 'test_name'])


class TestFinder(TestCase):

    def setUp(self):
        super(TestFinder, self).setUp()
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir)
        super(TestFinder, self).tearDown()

    def test_init(self):
        finder = salt.utils.find.Finder({})
        self.assertEqual(str(finder.actions[0].__class__)[-13:-2],
                    'PrintOption')
        self.assertEqual(finder.criteria, [])

        finder = salt.utils.find.Finder({'_': None})
        self.assertEqual(str(finder.actions[0].__class__)[-13:-2],
                    'PrintOption')
        self.assertEqual(finder.criteria, [])

        self.assertRaises(ValueError, salt.utils.find.Finder, {'': None})
        self.assertRaises(ValueError, salt.utils.find.Finder, {'name': None})
        self.assertRaises(ValueError, salt.utils.find.Finder, {'nonexist': 'somevalue'})

        finder = salt.utils.find.Finder({'name': 'test_name'})
        self.assertEqual(str(finder.actions[0].__class__)[-13:-2],
                    'PrintOption')
        self.assertEqual(str(finder.criteria[0].__class__)[-12:-2], 'NameOption')

        finder = salt.utils.find.Finder({'iname': 'test_name'})
        self.assertEqual(str(finder.actions[0].__class__)[-13:-2],
                    'PrintOption')
        self.assertEqual(str(finder.criteria[0].__class__)[-13:-2], 'InameOption')

        finder = salt.utils.find.Finder({'regex': '.*\.txt'})
        self.assertEqual(str(finder.actions[0].__class__)[-13:-2],
                    'PrintOption')
        self.assertEqual(str(finder.criteria[0].__class__)[-13:-2], 'RegexOption')

        finder = salt.utils.find.Finder({'iregex': '.*\.txt'})
        self.assertEqual(str(finder.actions[0].__class__)[-13:-2],
                    'PrintOption')
        self.assertEqual(str(finder.criteria[0].__class__)[-14:-2], 'IregexOption')

        finder = salt.utils.find.Finder({'type': 'd'})
        self.assertEqual(str(finder.actions[0].__class__)[-13:-2],
                    'PrintOption')
        self.assertEqual(str(finder.criteria[0].__class__)[-12:-2], 'TypeOption')

        finder = salt.utils.find.Finder({'owner': 'root'})
        self.assertEqual(str(finder.actions[0].__class__)[-13:-2],
                    'PrintOption')
        self.assertEqual(str(finder.criteria[0].__class__)[-13:-2], 'OwnerOption')

        finder = salt.utils.find.Finder({'group': 'root'})
        self.assertEqual(str(finder.actions[0].__class__)[-13:-2],
                    'PrintOption')
        self.assertEqual(str(finder.criteria[0].__class__)[-13:-2], 'GroupOption')

        finder = salt.utils.find.Finder({'size': '+1G'})
        self.assertEqual(str(finder.actions[0].__class__)[-13:-2],
                    'PrintOption')
        self.assertEqual(str(finder.criteria[0].__class__)[-12:-2], 'SizeOption')

        finder = salt.utils.find.Finder({'mtime': '1d'})
        self.assertEqual(str(finder.actions[0].__class__)[-13:-2],
                    'PrintOption')
        self.assertEqual(str(finder.criteria[0].__class__)[-13:-2], 'MtimeOption')

        finder = salt.utils.find.Finder({'grep': 'foo'})
        self.assertEqual(str(finder.actions[0].__class__)[-13:-2],
                    'PrintOption')
        self.assertEqual(str(finder.criteria[0].__class__)[-12:-2], 'GrepOption')

        finder = salt.utils.find.Finder({'print': 'name'})
        self.assertEqual(str(finder.actions[0].__class__)[-13:-2],
                    'PrintOption')
        self.assertEqual(finder.criteria, [])

    def test_find(self):
        hello_file = os.path.join(self.tmpdir, 'hello.txt')
        fd = open(hello_file, 'w')
        fd.write("foo")
        fd.close()

        finder = salt.utils.find.Finder({'name': 'test_name'})
        self.assertEqual(list(finder.find('')), [])

        finder = salt.utils.find.Finder({'name': 'hello.txt'})
        self.assertEqual(list(finder.find(self.tmpdir)), [hello_file])

        finder = salt.utils.find.Finder({'type': 'f', 'print': 'path'})
        self.assertEqual(list(finder.find(self.tmpdir)),
            [os.path.join(self.tmpdir, 'hello.txt')])

        finder = salt.utils.find.Finder({'size': '+1G', 'print': 'path'})
        self.assertEqual(list(finder.find(self.tmpdir)), [])

        finder = salt.utils.find.Finder({
            'name': 'hello.txt', 'print': 'path name'})
        self.assertEqual(list(finder.find(self.tmpdir)), [[hello_file, 'hello.txt']])


if __name__ == "__main__":
    loader = TestLoader()
    tests = loader.loadTestsFromTestCase(TestFind)
    tests.addTests(loader.loadTestsFromTestCase(TestGrepOption))
    tests.addTests(loader.loadTestsFromTestCase(TestPrintOption))
    tests.addTests(loader.loadTestsFromTestCase(TestFinder))
    TextTestRunner(verbosity=1).run(tests)