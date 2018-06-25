import xml.etree.ElementTree as ET
from os import walk
import os
import git
from difflib import Differ
from pprint import pprint
import subprocess

BASE_CHANGE_DIR = '/home/szamani/Desktop/term8/research/TemporaryFiles/{}'
FAILED_TESTS = 'failed_tests.txt'
BASE_DIR = '/home/szamani/Desktop/term8/research/repo/jgittest'
BASE_VERSION_DIR = '/home/szamani/Desktop/term8/research/repo/jgittest-version'
STATIC_ANALYSIS_PATH = '/home/szamani/Desktop/term8/research/java-callgraph/java-callgraph/target/javacg-0.1-SNAPSHOT-static.jar'
CHANGE_DISTILLER_PATH = '/home/szamani/Desktop/term8/changedistiller-jar/changedistiller/out/artifacts/changedistiller_jar/changedistiller.jar'
JAR_PATH = 'target/repo-1.0-SNAPSHOT.jar'
NEW = '-new'
OLD = '-old'


class RepoManagement:
    """
        if the repository is local, then `path` would be the local address of repository on disk
        if the repository is remote (on Github), then `path` would be the git address of repository on github,
            `remote` must be true and `directory_to_clone` would be the local address on disk to clone the repository
    """

    def __init__(self, path, remote=False, directory_to_clone=None):
        """
        maps the base_path of a version of repository to the direct call_graph of methods in that version
        note that this call_graph contains only direct calls so if `a` calls `b` and `c`, and `b` itself
            calls `d`, the call_graph of `a` would be [b, c], not [b, d, c]
        """
        self.path_call_graph = {}  # path: call_graph

        if remote:
            self.repo = git.Repo.clone(path, directory_to_clone)
            self.repo_address = directory_to_clone
        else:
            self.repo = git.Repo(path)
            self.repo_address = path

    def get_all_commits(self):
        """
        :return: a list of all commits for the self.repo
        """
        return list(self.repo.iter_commits('--all'))

    def get_commits_by_branch(self, branch):
        """
        :param branch: give the branch name you want the commits from
        :return:       a list of commits of that branch
        """
        return list(self.repo.iter_commits(branch))

    @staticmethod
    def get_files_changed_in_commit(commit):
        """
        :param commit: give a specific commit of the self.repo
        :return:       all the files changed in that commit (comparing to the previous version) and the details
                           deletion, insertion and total changed lines
        """
        return commit.stats.files

    @staticmethod
    def get_file_change_by_commit(commit, filename):
        """
        :param commit:    give a specific commit of the self.repo
        :param filename:  and a file that you want to know the details of its changes
        :return:          the details of changes happened to file or None
        """
        return commit.stats.files[filename] if filename in commit.stats.files else None

    @staticmethod
    def get_total_change_info_by_commit(commit):
        """
        :param commit: give a specific commit of the self.repo
        :return:       the whole details of changes happened in that commit
        """
        return commit.stats.total

    @staticmethod
    def get_files_present_in_commit(commit):
        """
        :param commit: give a specific commit of the self.repo
        :return:       all the file names that are present in this version of repo
        """
        return [entry.path for entry in
                commit.tree.traverse()]

    def get_file_content_in_commit(self, commit, filename):
        """
        :param commit:    give a specific commit of the self.repo
        :param filename:  and a filename you want the contents of it in that commit
        :return:          a string contains the exact content of the file in that commit
        """
        return self.repo.git.show('{}:{}'.format(commit.hexsha, filename))

    def get_files_content_in_commit(self, commit):
        """
        :param commit: give a specific commit of the self.repo
        :return:       a list of all the file contents
        """
        return {entry.path: self.repo.git.show('{}:{}'.format(commit.hexsha, entry.path)) for entry in
                commit.tree.traverse()}

    def get_file_content_diff_between_commits(self, commit1, commit2, filename):
        """
        :param commit1:  specify the first commit
        :param commit2:  and the second commit
        :param filename: and the filename you want the difference between its content in two versions
        :return:         a list of differences between the the file contents in two versions
        """
        file_content1 = self.get_file_content_in_commit(commit1, filename).splitlines()
        file_content2 = self.get_file_content_in_commit(commit2, filename).splitlines()
        d = Differ()
        pprint(list(d.compare(file_content1, file_content2)))
        return list(d.compare(file_content1, file_content2))

    def get_file_content_diff_in_commit(self, commit, filename1, filename2):
        """
        :param commit:    specify a commit
        :param filename1: and the first file
        :param filename2: and the second file you want the difference between them in the specific commit
        :return:          a list of differences
        """
        file1_content = self.get_file_content_in_commit(commit, filename1).splitlines()
        file2_content = self.get_file_content_in_commit(commit, filename2).splitlines()
        d = Differ()
        pprint(list(d.compare(file1_content, file2_content)))
        return list(d.compare(file1_content, file2_content))

    @staticmethod
    def get_file_contents_diff(file1, file2):
        """
        Nothing special about this method
        :param file1: specify first file content
        :param file2: and the second file content
        :return:      a list of differences
        """
        d = Differ()
        pprint(list(d.compare(file1, file2)))
        return list(d.compare(file1, file2))

    @staticmethod
    def save_to_file(filename, content):
        """
        Nothing special about this method
        :param filename: specify the filename you want to save on disk
        :param content:  and its content
        """
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        with open(filename, 'w') as f:
            f.write(content)

    def save_modified_files_between_consecutive_commits(self, earlier_commit, former_commit):
        """
        Given two consecutive commits for example the nth and (n-1)th commit, this method will find all the
        modified files between the two commits and save the older version and the newer version into BASE_CHANGE_DIR.
        The older version is saved with -old at the end of filename and the newer one with -new.
        :param earlier_commit: specify the first commit
        :param former_commit:  specify the second commit
        :return:               Nothing (save the result into file)
        """

        # use the self.get_files_changed_in_commit() method to find the changed files in this commit (this is the reason
        # why the two commits must be consecutive). Then for each changed file, find its content using the
        # self.get_file_content_in_commit() method and finally save them with -old and -new name extension.
        for file_changed_in_commit in self.get_files_changed_in_commit(earlier_commit):
            original = file_changed_in_commit
            file_changed_in_commit = file_changed_in_commit.replace(
                file_changed_in_commit[:file_changed_in_commit.rfind('.java')],
                file_changed_in_commit[:file_changed_in_commit.rfind('.java')] + NEW)
            self.save_to_file(BASE_CHANGE_DIR.format(file_changed_in_commit),
                              self.get_file_content_in_commit(earlier_commit, original))

        for file_changed_in_commit in self.get_files_changed_in_commit(earlier_commit):
            original = file_changed_in_commit
            file_changed_in_commit = file_changed_in_commit.replace(
                file_changed_in_commit[:file_changed_in_commit.rfind('.java')],
                file_changed_in_commit[:file_changed_in_commit.rfind('.java')] + OLD)
            self.save_to_file(BASE_CHANGE_DIR.format(file_changed_in_commit),
                              self.get_file_content_in_commit(former_commit, original))

    def run_test_suit(self):
        """
        run the test suit (maven project and Junit test suite) in the self.repo_address.
        Could be modified to run the test suite in given path which then could contain another version,
        but for now only the latest version is needed.
        :return: Nothing
        """
        subprocess.run(['mvn', 'test', '-f', self.repo_address]
                       , stdout=subprocess.PIPE)

    def extract_failed_tests(self, extension_path):
        """
        Find the failing tests (maven project and Junit test suite) and save their name into a file in BASE_CHANGE_DIR
        Note that in a normal maven project with Junit, the result of the latest test run is stored in
        target/surefire-reports as xml files but this path is given as the extension_path argument
        :param extension_path: the relative path of where the test results are saved
        :return:               Nothing
        """
        failed_tests = []
        test_result_files = []

        # test results are saved as xml in this path. let's find all of the xml files in the path
        for (dirpath, dirname, filename) in walk(os.path.join(self.repo_address, extension_path)):
            test_result_files.extend(list(filter(lambda x: x.endswith('.xml'), filename)))
            break
        # join the path with the base address to have the absolute path of test results
        test_result_files = list(map(lambda x: os.path.join(self.repo_address, extension_path, x), test_result_files))

        # Parse the xml file to extract the failing tests
        for test_result in test_result_files:
            tree = ET.parse(test_result)
            root = tree.getroot()
            for child in root.findall('testcase'):
                if len(child) != 0:
                    # package.address.ClassName:MethodName() ==> Assume that no arguments for @Test methods
                    failed_tests.append('{}:{}()'.format(child.attrib['classname'], child.attrib['name']))

        pprint(failed_tests)

        # finally save them into a predefined path
        with open(BASE_CHANGE_DIR.format(FAILED_TESTS), 'w') as f:
            f.writelines(failed_tests)
        return failed_tests

    def save_older_version_of_project(self, earlier_commit, former_commit):
        """
        WARNING: Works for the latest commit for now, i.e. only works when you want to save the previous version
                 of project than the final version.

        In order to extract call_graph or other information from an older version of the project, we need to save
        that version into disk to run analysis on them. note that earlier_commit and former_commit must be
        consecutive. Given that we want to save the (n-1)th commit, we need to send nth commit and (n-1)th commit
        as earlier_commit and former_commit respectively as the arguments.

        To have a sense of why the earlier commit is needed to save the former commit, pay attention to the procedure
        of this method.
        First an exact copy of the latest project is created in a new predefined path.
        Second using the two consecutive commits the modified files are found and replaced with the original ones
        :param earlier_commit: nth commit
        :param former_commit:  (n-1)th commit which we actually want to save into disk.
        :return:               Nothing
        """

        # Make a copy of the latest version
        subprocess.run(['cp', '-r', BASE_DIR, BASE_VERSION_DIR],
                       stdout=subprocess.PIPE)

        # Using the self.get_files_changed_in_commit() method, all modified files are overwritten with the
        # former version
        for file_changed in self.get_files_changed_in_commit(earlier_commit):
            self.save_to_file(os.path.join(BASE_VERSION_DIR, file_changed),
                              self.get_file_content_in_commit(former_commit, file_changed))

    def create_jar_of_project(self, project_path=None):  # mvn package -Dmaven.test.failure.ignore=true
        """
        For now, in order to perform a static call_graph analysis the jar file of the project is needed,
        so this method does that.
        :param project_path: path of the project to create jar from, if not set the latest version is considered.
        :return:             Nothing
        """

        if not project_path:
            project_path = self.repo_address

        # The last option tells maven to ignore the test results
        # and save the project as a jar file whether of not a test fails
        subprocess.run(['mvn', 'package', '-Dmaven.test.failure.ignore=true']
                       , stdout=subprocess.PIPE, cwd=project_path)

    def create_call_graph(self, path):
        """
        Use [java-callgraph](https://github.com/gousiosg/java-callgraph) to perform a static analysis
        and find the callee methods in all methods.
        One IMPORTANT point to notice is that the returned dictionary ONLY contains the direct calls
        :param path: is used to save the result into self.path_call_graph dictionary
        :return:     caller_callee_dict ==> {"caller_method_signature": ["callee_method_signature1",
                                                                         "callee_method_signature2",
                                                                         "callee_method_signature3",...]}
        """
        call_graph_res = subprocess.run(['java', '-jar', STATIC_ANALYSIS_PATH, os.path.join(path, JAR_PATH)],
                                        stdout=subprocess.PIPE)
        call_graph_res = call_graph_res.stdout.decode('utf-8')
        caller_callee_dict = {}  # caller: callee

        """
            Every line of the `java-callgraph` static analysis output is structured like this:
            
            M:class1:<method1>(arg_types) (typeofcall)class2:<method2>(arg_types)
            
            The line means that method1 of class1 called method2 of class2. The type of call 
            can have one of the following values:
                M for invokevirtual calls
                I for invokeinterface calls
                O for invokespecial calls
                S for invokestatic calls
                D for invokedynamic calls
        """
        for line in call_graph_res.splitlines():
            if line.startswith('M'):
                caller = line.split(' ')[0][2:]
                callee = line.split(' ')[1][3:]
                if caller in caller_callee_dict:
                    caller_callee_dict[caller].append(callee)
                else:
                    caller_callee_dict[caller] = [callee]

        self.path_call_graph[path] = caller_callee_dict
        return caller_callee_dict

    def get_method_call_chain(self, ccd, method_name, result):
        """
        Given a method name and a dictionary of method caller and callee like:
        "caller_method": ["callee_method1", "callee_method2", ...]
        calculate the dfs of it's call graph and returns it as a list
        :param ccd:         caller callee dictionary
        :param method_name: method name to dfs traverse taking it as root node in call graph
        :param result:      the result of above procedure
        :return:            the result of above procedure
        """
        if method_name not in ccd:  # system and library methods are assumed to have no bugs to cause a test failure
            return
        if len(result) > 1 and result[-1] == result[-2]:  # handling recursive calls
            return
        for callee in ccd[method_name]:
            result.append(callee)
            self.get_method_call_chain(ccd, callee, result)
        return result

    def find_method_chain_in_failing_tests(self, cc_dict):
        """
        for every failing test compute the dfs traverse of it's call graph.
        :param cc_dict: caller callee dictionary
        :return:        A dictionary like this:
                            {"failing_test1": ["callee_method1", "callee_method2", ...],
                             "failing_test2": ["callee_method1", "callee_method2", ...]}
        """
        failing_tests_result = {}  # failing_test: sequence of called methods
        with open(BASE_CHANGE_DIR.format(FAILED_TESTS), 'r') as f:
            failing_tests = f.readlines()

        for ft in failing_tests:
            result = []
            self.get_method_call_chain(cc_dict, ft, result)
            failing_tests_result[ft] = result

        pprint(failing_tests_result)
        return failing_tests_result

    @staticmethod
    def extract_change_between_two_files(path1, path2):
        changes = subprocess.run(['java', '-jar', CHANGE_DISTILLER_PATH, path1, path2],
                                 stdout=subprocess.PIPE)
        changes = changes.stdout.decode('utf-8')
        pprint(changes)
        return changes


if __name__ == '__main__':
    r = RepoManagement(BASE_DIR)

    # pprint(r.get_files_changed_in_commit(r.get_all_commits()[0]))
    # pprint(r.get_files_present_in_commit(r.get_all_commits()[2]))
    # pprint(r.get_file_change_by_commit(r.get_all_commits()[0], 'pom.xml'))
    # pprint(r.get_file_content_in_commit(r.get_all_commits()[0], 'pom.xml'))
    # pprint(r.get_files_content_in_commit(r.get_all_commits()[0]))
    # print(r.get_file_content_diff_between_commits(r.get_all_commits()[0],
    #                                                r.get_all_commits()[2],
    #                                                'src/main/java/ir/szamani/Calculator.java'))

    # r.save_modified_files_between_consecutive_commits(r.get_all_commits()[0], r.get_all_commits()[1])
    #
    # r.run_test_suit()
    # r.extract_failed_tests('target/surefire-reports')
    # r.save_older_version_of_project(r.get_all_commits()[0], r.get_all_commits()[1])
    # r.create_jar_of_project(BASE_DIR)
    # r.create_jar_of_project(BASE_VERSION_DIR)
    caller_callee_dict = r.create_call_graph(BASE_DIR)
    dfs_failing_test = r.find_method_chain_in_failing_tests(caller_callee_dict)  # the actual failing test

    caller_callee_dict_version = r.create_call_graph(BASE_VERSION_DIR)
    dfs_failing_test_version = r.find_method_chain_in_failing_tests(
        caller_callee_dict_version)  # the test that used to pass

    r.extract_change_between_two_files('/home/szamani/Desktop/term8/research/TemporaryFiles/src/main/java/ir/szamani/Sort-old.java',
                                       '/home/szamani/Desktop/term8/research/TemporaryFiles/src/main/java/ir/szamani/Sort-new.java')

    """
    The main problem with change_distiller is that it only works at file level (does it?) i.e. we cannot feed it with 
    two methods that the caller_callee_dict say that there was a change and expect any result.
    One other option is using git diff tool or other diff tools. That could be a wise choice when the tool
    is designed for JAVA so that it will tell us about the changes with more details.
    """
