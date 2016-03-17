import unittest
import env
import os
import shutil
import json
from time import sleep
from collections import namedtuple
from queue.scanner import Scanner
from queue.scanner import rf_table_name, lib_table_name
from index.index import Index


class TestIndexing(unittest.TestCase):

    """The content of the db_fir was created with scanner by scanning the
    TEST_DATA_DIR/suite_tree folder. If scanner is changed, db_dir must
    be recreated."""

    @classmethod
    def setUpClass(cls):
        cls.db_dir = os.path.join(
            env.RESULTS_DIR,
            'db_dir'
        )
        cls.suite_dir = os.path.join(
            env.TEST_DATA_DIR,
            'suite_tree'
        )
        scanner = Scanner()
        scanner.scan(
            cls.suite_dir,
            'robot',
            cls.db_dir)

    def setUp(self):
        self.index_dir = os.path.join(
            env.RESULTS_DIR,
            'index_dir',
        )
        if os.path.exists(self.index_dir):
            while os.path.exists(self.index_dir):
                shutil.rmtree(self.index_dir)
                sleep(0.1)
        os.makedirs(self.index_dir)
        self.index = Index(self.index_dir)

    def test_parse_table_data(self):
        t_name = os.path.join(
            env.RESOURCES_DIR,
            'BuiltIn-ca8f2e8d70641ce17b9b304086c19657.json'
        )
        self.index.queue.add(t_name, None, None)
        data, status = self.index.read_table(
            os.path.join(env.RESOURCES_DIR, t_name))
        var, kw_index = self.index.parse_table_data(data, t_name)
        self.assertTrue(u'${/}' in var)
        self.assertTrue('${OUTPUT_FILE}' in var)
        self.assertTrue('@{TEST_TAGS}' in var)

    def test_add_builtin(self):
        self.index.add_builtin_to_queue(self.db_dir)
        self.assertTrue(len(self.index.queue.queue) > 0)

    def test_read_table(self):
        data, read_status = self.index.read_table(
            os.path.join(
                self.db_dir,
                self.test_b_table_name))
        self.assertTrue(data['file_name'], 'test_b.robot')

    def test_get_keywords_resource(self):
        data = self.get_resource_b()
        expected_kw_list = ['Resource B Keyword 2', 'Resource B Keyword 1']
        expected_arg_list = [['kwb1'], []]
        kw_list, arg_list = self.index.get_keywords(data)
        self.assertEqual(kw_list, expected_kw_list)
        self.assertEqual(arg_list.sort(), expected_arg_list.sort())

        data = self.get_test_a()
        expected_kw_list = ['Test A Keyword']
        kw_list, arg_list = self.index.get_keywords(data)
        self.assertEqual(kw_list, expected_kw_list)
        self.assertEqual(arg_list, [[]])

        data = self.get_s2l()
        parsed_kw, arg_list = self.index.get_keywords(data)
        self.assertTrue('Set Window Position' in parsed_kw)
        self.assertTrue('Get Cookies' in parsed_kw)
        self.assertTrue('Unselect Frame' in parsed_kw)
        self.assertTrue(['name'] in arg_list)
        l = ['driver_name', 'alias', 'kwargs', '**init_kwargs']
        self.assertTrue(l in arg_list)
        self.assertTrue(['*code'] in arg_list)

    def test_get_imports(self):
        data = self.get_resource_b()
        import_list = [self.process_table_name]
        self.assertEqual(self.index.get_imports(data), import_list)

        data = self.get_test_a()
        import_list = [
            self.common_table_name,
            self.resource_a_table_name]
        self.assertEqual(
            self.index.get_imports(data).sort(), import_list.sort())

        data = self.get_s2l()
        self.assertEqual(self.index.get_imports(data), [])

    def test_get_variables(self):
        data = self.get_resource_b()
        var = ['${RESOURCE_B}']
        self.assertEqual(self.index.get_variables(data), var)

        data = self.get_test_a()
        var = ['${TEST_A}']
        self.assertEqual(
            self.index.get_variables(data).sort(), var.sort())

        data = self.get_s2l()
        self.assertEqual(self.index.get_variables(data), [])

        data = self.get_common()
        self.assertEqual(self.index.get_variables(data), [])

    def test_get_kw_for_index(self):
        KeywordRecord = namedtuple(
            'KeywordRecord',
            'keyword argument object_name table_name')
        table_name = self.resource_b_table_name
        l, kw_list, arg_list, object_name, table_name = \
            self.get_resource_b_kw_index(KeywordRecord)

        self.assertEqual(
            self.index.get_kw_for_index(
                kw_list, arg_list, table_name, object_name), l)

        l, kw_list, arg_list, object_name, table_name = \
            self.get_test_a_kw_index(KeywordRecord)
        self.assertEqual(
            self.index.get_kw_for_index(
                kw_list, arg_list, table_name, object_name), l)

        l, kw_list, arg_list, object_name, table_name = self.get_s2l_kw_index(
            KeywordRecord)
        self.assertEqual(
            self.index.get_kw_for_index(
                kw_list, arg_list, table_name, object_name), l)

    def test_index_creation_test_a(self):
        table_name = self.test_a_table_name
        KeywordRecord = namedtuple(
            'KeywordRecord',
            'keyword argument object_name table_name')
        kw_list = []
        kw_list.extend(self.get_test_a_kw_index(KeywordRecord)[0])
        kw_list.extend(self.get_common_kw_index(KeywordRecord)[0])
        kw_list.extend(self.get_resource_a_kw_index(KeywordRecord)[0])
        kw_list.extend(self.get_s2l_kw_index(KeywordRecord)[0])
        kw_list.extend(self.get_os_kw_index(KeywordRecord)[0])
        kw_list.extend(self.get_builtin_kw_index(KeywordRecord)[0])
        kw_list.extend(self.get_LibNoClass_kw_index(KeywordRecord)[0])
        var_list = [
            u'${TEST_A}',
            u'${RESOURCE_A}',
            u'${COMMON_VARIABLE_1}',
            u'${COMMON_VARIABLE_2}'
        ]
        t_index = {
            'keyword': kw_list,
            'variable': var_list}
        r_index = self.index.create_index_for_table(self.db_dir, table_name)
        self.assertEqual(
            r_index['variable'].sort(), t_index['variable'].sort())
        self.assertEqual(len(r_index['keyword']), len(t_index['keyword']))
        self.assertEqual(r_index['keyword'].sort(), t_index['keyword'].sort())

    def test_index_creation_test_b(self):
        table_name = self.test_b_table_name
        KeywordRecord = namedtuple(
            'KeywordRecord',
            'keyword argument object_name table_name')
        kw_list = []
        kw_list.extend(self.get_test_b_kw_index(KeywordRecord)[0])
        kw_list.extend(self.get_common_kw_index(KeywordRecord)[0])
        kw_list.extend(self.get_resource_b_kw_index(KeywordRecord)[0])
        kw_list.extend(self.get_s2l_kw_index(KeywordRecord)[0])
        kw_list.extend(self.get_process_kw_index(KeywordRecord)[0])
        kw_list.extend(self.get_builtin_kw_index(KeywordRecord)[0])
        var_list = [
            u'${TEST_B}',
            u'${RESOURCE_B}',
            u'${COMMON_VARIABLE_1}',
            u'${COMMON_VARIABLE_2}'
        ]
        t_index = {
            'keyword': kw_list,
            'variable': var_list}
        r_index = self.index.create_index_for_table(self.db_dir, table_name)
        self.assertEqual(
            r_index['variable'].sort(), t_index['variable'].sort())
        self.assertEqual(len(r_index['keyword']), len(t_index['keyword']))
        self.assertEqual(r_index['keyword'].sort(), t_index['keyword'].sort())

    def test_index_all_db(self):
        t_index_table_names = []
        for table in os.listdir(self.db_dir):
            t_index_table_names.append(
                'index-{0}'.format(table))
        self.index.index_all_tables(self.db_dir)
        r_index_table_names = os.listdir(self.index_dir)
        self.assertEqual(r_index_table_names, t_index_table_names)
        for index_file in os.listdir(self.index_dir):
            size = os.path.getsize(os.path.join(self.index_dir, index_file))
            self.assertGreater(size, 10)

    def test_get_kw_arguments(self):
        kw_args = [u'item', u'msg=None']
        result = self.index.get_kw_arguments(kw_args)
        expected = [u'item', u'msg']
        self.assertEqual(result, expected)
        kw_args = [u'name', u'*args']
        result = self.index.get_kw_arguments(kw_args)
        self.assertEqual(result, kw_args)
        kw_args = []
        result = self.index.get_kw_arguments(kw_args)
        self.assertEqual(result, kw_args)
        kw_args = [u'object=None', u'*args', u'**kwargs']
        result = self.index.get_kw_arguments(kw_args)
        expected = [u'object', u'*args', u'**kwargs']
        self.assertEqual(result, expected)
        kw_args = [u'${kwa1}', '@{list}', '&{kwargs}']
        result = self.index.get_kw_arguments(kw_args)
        expected = [u'kwa1', '*list', '**kwargs']
        self.assertEqual(result, expected)

    def test_real_suite(self):
        self.real_suite_dir = os.path.join(
            env.TEST_DATA_DIR,
            'real_suite'
        )
        scanner = Scanner()
        scanner.scan(
            self.real_suite_dir,
            'robot',
            self.db_dir)
        self.index.index_all_tables(self.db_dir)
        r_index_table_names = os.listdir(self.index_dir)
        self.assertEqual(len(r_index_table_names), 8)
        real_suite_index = 'index-{0}'.format(self.real_suite_table_name)
        f = open(os.path.join(self.index_dir, real_suite_index))
        data = json.load(f)
        f.close()
        kw_names = [kw_list[0] for kw_list in data['keyword']]
        self.assertIn('Run Keyword And Expect Error', kw_names)
        self.assertIn('Open Browser', kw_names)

    def test_cache_creation(self):
        self.assertEqual(len(self.index.cache), 0)
        self.index.index_all_tables(self.db_dir)
        self.assertIn(self.common_table_name_index, self.index.cache)
        self.assertIn(self.test_a_table_name_index, self.index.cache)

    def test_get_data_from_created_index(self):
        self.index.index_all_tables(self.db_dir)
        keywords, variables, tables = self.index.get_data_from_created_index(
            self.test_a_table_name_index)
        self.assertIn(self.builtin_table_name, tables)
        self.assertIn('${TEST_A}', variables)
        test_a_keyword = [
            'Test A Keyword',
            [],
            'test_a.robot',
            self.test_a_table_name
        ]
        self.assertIn(test_a_keyword, keywords)

    def test_add_table_to_index(self):
        test_a_index = os.path.join(
            env.TEST_DATA_DIR,
            '..',
            'index-test_a.robot-41883aa9e5af28925d37eba7d2313d57.json')
        keywords, variables, tables = self.index.get_data_from_created_index(
            test_a_index)
        self.assertEqual(len(self.index.queue.queue), 0)
        self.index.add_table_to_index(tables, self.db_dir)
        self.assertEqual(len(self.index.queue.queue), 6)

    @property
    def common_table_name_index(self):
        index = 'index-{0}'.format(self.common_table_name)
        return os.path.join(self.index_dir, index)

    @property
    def test_a_table_name_index(self):
        index = 'index-{0}'.format(self.test_a_table_name)
        return os.path.join(self.index_dir, index)

    @property
    def real_suite_table_name(self):
        return rf_table_name(
            os.path.normcase(
                os.path.join(
                    self.real_suite_dir,
                    'test',
                    'real_suite.robot'
                )
            )
        )

    @property
    def resource_b_table_name(self):
        return rf_table_name(
            os.path.normcase(os.path.join(self.suite_dir, 'resource_b.robot'))
        )

    @property
    def common_table_name(self):
        return rf_table_name(
            os.path.normcase(os.path.join(self.suite_dir, 'common.robot'))
        )

    @property
    def test_a_table_name(self):
        return rf_table_name(
            os.path.normcase(os.path.join(self.suite_dir, 'test_a.robot'))
        )

    @property
    def test_b_table_name(self):
        return rf_table_name(
            os.path.normcase(os.path.join(self.suite_dir, 'test_b.robot'))
        )

    @property
    def resource_a_table_name(self):
        return rf_table_name(os.path.normcase(
            os.path.join(self.suite_dir, 'resource_a.robot'))
        )

    @property
    def s2l_table_name(self):
        return lib_table_name('Selenium2Library')

    @property
    def os_table_name(self):
        return lib_table_name('OperatingSystem')

    @property
    def process_table_name(self):
        return lib_table_name('Process')

    @property
    def builtin_table_name(self):
        return lib_table_name('BuiltIn')

    @property
    def libnoclass_table_name(self):
        return lib_table_name('LibNoClass')

    def get_resource_b(self):
        f = open(os.path.join(
                    self.db_dir,
                    self.resource_b_table_name
                )
            )
        return json.load(f)

    def get_common(self):
        f = open(os.path.join(
                self.db_dir,
                self.common_table_name
            )
        )
        return json.load(f)

    def get_test_a(self):
        f = open(os.path.join(
                self.db_dir,
                self.test_a_table_name
            )
        )
        return json.load(f)

    def get_s2l(self):
        f = open(os.path.join(
                self.db_dir,
                self.s2l_table_name
            )
        )
        return json.load(f)

    def get_os(self):
        f = open(os.path.join(
                self.db_dir,
                self.os_table_name
            )
        )
        return json.load(f)

    def get_process(self):
        f = open(os.path.join(
                self.db_dir,
                self.process_table_name
            )
        )
        return json.load(f)

    def getbuiltin(self):
        f = open(os.path.join(
                self.db_dir,
                self.builtin_table_name
            )
        )
        return json.load(f)

    def get_libnoclass(self):
        f = open(os.path.join(
                self.db_dir,
                self.libnoclass_table_name
            )
        )
        return json.load(f)

    def get_s2l_kw_index(self, keywordrecord):
        s2l_data = self.get_s2l()
        kw_list = self.index.get_keywords(s2l_data)[0]
        arg_list = self.get_kw_args(s2l_data)
        object_name = 'Selenium2Library'
        table_name = self.s2l_table_name
        l = []
        for kw, arg in zip(kw_list, arg_list):
            l.append(
                keywordrecord(
                    keyword=kw,
                    argument=arg,
                    object_name=object_name,
                    table_name=table_name
                )
            )
        return l, kw_list, arg_list, object_name, table_name

    def get_os_kw_index(self, keywordrecord):
        os_data = self.get_os()
        kw_list = self.index.get_keywords(os_data)[0]
        arg_list = self.get_kw_args(os_data)
        object_name = 'OperatingSystem'
        table_name = self.os_table_name
        l = []
        for kw, arg in zip(kw_list, arg_list):
            l.append(
                keywordrecord(
                    keyword=kw,
                    argument=arg,
                    object_name=object_name,
                    table_name=table_name
                )
            )
        return l, kw_list, arg_list, object_name, table_name

    def get_process_kw_index(self, keywordrecord):
        data = self.get_process()
        kw_list = self.index.get_keywords(data)[0]
        arg_list = self.get_kw_args(data)
        object_name = 'Process'
        table_name = self.process_table_name
        l = []
        for kw, arg in zip(kw_list, arg_list):
            l.append(
                keywordrecord(
                    keyword=kw,
                    argument=arg,
                    object_name=object_name,
                    table_name=table_name
                )
            )
        return l, kw_list, arg_list, object_name, table_name

    def get_builtin_kw_index(self, keywordrecord):
        data = self.getbuiltin()
        kw_list = self.index.get_keywords(data)[0]
        arg_list = self.get_kw_args(data)
        object_name = 'BuiltIn'
        table_name = self.builtin_table_name
        l = []
        for kw, arg in zip(kw_list, arg_list):
            l.append(
                keywordrecord(
                    keyword=kw,
                    argument=arg,
                    object_name=object_name,
                    table_name=table_name
                )
            )
        return l, kw_list, arg_list, object_name, table_name

    def get_LibNoClass_kw_index(self, keywordrecord):
        data = self.get_libnoclass()
        kw_list = self.index.get_keywords(data)[0]
        arg_list = self.get_kw_args(data)
        object_name = 'BuiltIn'
        table_name = self.builtin_table_name
        l = []
        for kw, arg in zip(kw_list, arg_list):
            l.append(
                keywordrecord(
                    keyword=kw,
                    argument=arg,
                    object_name=object_name,
                    table_name=table_name
                )
            )
        return l, kw_list, arg_list, object_name, table_name

    def get_test_a_kw_index(self, keywordrecord):
        kw_list = [u'Test A Keyword']
        table_name = self.test_a_table_name
        object_name = u'test_a.robot'
        l = [keywordrecord(
            keyword=kw_list[0],
            argument=None,
            object_name=object_name,
            table_name=table_name)]
        return l, kw_list, [None], object_name, table_name

    def get_test_b_kw_index(self, keywordrecord):
        kw_list = []
        table_name = self.test_b_table_name
        object_name = u'test_a.robot'
        l = []
        return l, kw_list, [None], object_name, table_name

    def get_resource_a_kw_index(self, keywordrecord):
        kw_list = [u'Resource A Keyword 1', u'resource A Keyword 2']
        arg_list = ['kwa1', None]
        table_name = self.resource_a_table_name
        object_name = u'resource_a.robot'
        l = []
        for kw, arg in zip(kw_list, arg_list):
            l.append(
                keywordrecord(
                    keyword=kw,
                    argument=arg,
                    object_name=object_name,
                    table_name=table_name
                )
            )
        return l, kw_list, arg_list, object_name, table_name

    def get_resource_b_kw_index(self, keywordrecord):
        kw_list = [u'Resource B Keyword 1', u'resource B Keyword 2']
        arg_list = ['kwb1', None]
        table_name = self.resource_b_table_name
        object_name = u'resource_b.robot'
        l = []
        for kw, arg in zip(kw_list, arg_list):
            l.append(
                keywordrecord(
                    keyword=kw,
                    argument=arg,
                    object_name=object_name,
                    table_name=table_name
                )
            )
        return l, kw_list, arg_list, object_name, table_name

    def get_common_kw_index(self, keywordrecord):
        kw_list = [u'Common Keyword 2', u'common Keyword 1']
        table_name = self.common_table_name
        object_name = u'common.robot'
        l = []
        for kw in kw_list:
            l.append(
                keywordrecord(
                    keyword=kw,
                    argument=None,
                    object_name=object_name,
                    table_name=table_name
                )
            )
        return l, kw_list, [None], object_name, table_name

    def get_kw_args(self, data):
        arg_list = []
        kws = data["keywords"]
        for i in kws.iterkeys():
            args = kws[i]['keyword_arguments']
            for arg in args:
                if '=' in arg:
                    arg_list.append(arg.split('=')[0])
                else:
                    arg_list.append(arg)
        return arg_list
