import pprint
from difflib import Differ

from git import Repo

repo = Repo('/home/szamani/Desktop/term8/research/repo')
commits = list(repo.iter_commits('--all'))

# for entry in commits[3].tree.traverse():
#     print(str(entry.name))
#     print(str(entry.mode))
#     print(str(entry.type))
#     print(str(entry.abspath))
#     print(str(entry.path))
#     print(str(entry.size))
#     print(type(entry))
#     print('###########\n\n')

# for entry in commits[2].tree.traverse():
#     print(str(entry.abspath.strip()))
#     file_contents = repo.git.show('{}:{}'.format(commits[2].hexsha, entry.path))
#     print(file_contents)
#     print('##########')

read_me_1 = repo.git.show('{}:{}'.format(commits[2].hexsha, 'src/main/java/ir/szamani/Main.java')).splitlines()
read_me_2 = repo.git.show('{}:{}'.format(commits[3].hexsha, 'src/main/java/ir/szamani/Main.java')).splitlines()
print(read_me_1)
print(read_me_2)
d = Differ()
pprint.pprint(list(d.compare(read_me_1, read_me_2)))

# print(repo.git.diff(commits[0], commits[1]))


# print(commits[0].stats.total)
# print(commits[2].stats.files)
