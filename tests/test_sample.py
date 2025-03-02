# Copyright (C) 2016, 2024 Ben North
#
# This file is part of literate-git tools --- render a literate git repository
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import bs4
import pygit2 as git
import pytest
import hashlib
from pathlib import Path

from literategit.cli.render import render_
import literategit.dump_all_trees


tamagotchi_github_url = 'https://github.com/bennorth/webapp-tamagotchi.git'


@pytest.fixture(scope='session')
def local_repo(tmpdir_factory):
    repo_root = str(tmpdir_factory.mktemp('repo'))
    repo = git.clone_repository('.', repo_root, checkout_branch='sample-history-for-tests')
    branch = repo.lookup_branch('origin/initial-empty-state', git.GIT_BRANCH_REMOTE)
    commit = repo[branch.target]
    repo.create_branch('start', commit)
    branch = repo.lookup_branch('origin/test-point-without-docs', git.GIT_BRANCH_REMOTE)
    commit = repo[branch.target]
    repo.create_branch('test-point-without-docs', commit)
    return repo


def maybe_dump(fname_prefix, text):
    """
    Use the env.var LITGIT_TEST_DUMP_FNAME_SUFFIX to request
    that the output used in the regression tests be dumped to files.
    For example,

        LITGIT_TEST_DUMP_FNAME_SUFFIX="-new.txt" poetry run pytest tests

    will generate files

        TestLocalRepo-new.txt
        TestTamagotchi-new.txt

    containing the rendered output of the two tests.  This eases the job
    of comparing old to new rendering, when checking that only expected
    changes have happened before updating the regression test hashes.
    """
    maybe_fname_suffix = os.getenv('LITGIT_TEST_DUMP_FNAME_SUFFIX')
    if maybe_fname_suffix:
        fname = '{}{}'.format(fname_prefix, maybe_fname_suffix)
        with open(fname, 'wt') as f_out:
            f_out.write(text)


class UsingLocalRepo:
    def rendered_output(self, local_repo, create_url):
        args = ['My cool project', 'start', 'sample-history-for-tests',
                create_url, True]

        output_list = []
        render_(*args, _path=local_repo.path, _print=output_list.append)

        assert len(output_list) == 1
        output_text = output_list[0]

        return output_text


class TestLocalRepo(UsingLocalRepo):
    def test_render(self, local_repo):
        output_text = self.rendered_output(
            local_repo,
            'literategit.example_create_url.CreateUrl')

        maybe_dump('TestLocalRepo', output_text)

        assert 'Add documentation' in output_text
        assert 'Add <code>colours</code> submodule' in output_text

        # Regression test.  The previous two asserts are therefore unnecessary
        # (as long as they passed while setting this hash), but leaving them in
        # for clarity.
        #
        output_hash = hashlib.sha256(output_text.encode()).hexdigest()
        exp_hash = '5e7109a991714b79bd4b2eb3cb9c7e4b7ace193c3a9b282745f6a3f779011116'
        assert output_hash == exp_hash


class TestUrlEscaping(UsingLocalRepo):
    def test_render(self, local_repo):
        output_text = self.rendered_output(
            local_repo,
            'literategit.example_create_url.CreateQueryUrl')

        maybe_dump('TestUrlEscaping', output_text)

        soup = bs4.BeautifulSoup(output_text, 'html.parser')
        result_as = soup.find_all('a', string='RESULT')
        assert len(result_as) == 15
        for a in result_as:
            assert 'blue&sha1' not in str(a)
            assert 'blue&amp;sha1' in str(a)


@pytest.fixture(scope='session')
def tamagotchi_repo(tmpdir_factory):
    repo_root = str(tmpdir_factory.mktemp('repo'))
    repo = git.clone_repository(tamagotchi_github_url, repo_root, checkout_branch='for-rendering')
    branch = repo.lookup_branch('origin/start', git.GIT_BRANCH_REMOTE)
    commit = repo[branch.target]
    repo.create_branch('start', commit)
    return repo


class TestTamagotchi:
    def test_render(self, tamagotchi_repo):
        """
        This is fragile in that it relies on the exact state of the 'Tamagotchi'-style
        webapp repo, but it does at least check all the parts fit together.
        """
        args = ['My cool project', 'start', 'for-rendering', 'literategit.example_create_url.CreateUrl', True]
        output_list = []
        render_(*args, _path=tamagotchi_repo.path, _print=output_list.append)

        assert len(output_list) == 1
        output_text = output_list[0]

        maybe_dump('TestTamagotchi', output_text)

        soup = bs4.BeautifulSoup(output_text, 'html.parser')
        node_divs = soup.find_all('div', class_='literate-git-node')
        got_sha1s = sorted(d.attrs['data-commit-sha1'] for d in node_divs)

        exp_commits = literategit.dump_all_trees.collect_commits(tamagotchi_repo,
                                                                 'start',
                                                                 'for-rendering')
        exp_sha1s = sorted(str(c.id) for c in exp_commits)

        assert got_sha1s == exp_sha1s
        assert len(got_sha1s) == 162  # More fragility

        # Regression test.
        output_hash = hashlib.sha256(output_text.encode()).hexdigest()
        exp_hash = '5d8d4be841e4c255e2c58e0710ce40dc13e8aee56eb038e8015cecaa06a4d34f'
        assert output_hash == exp_hash


class TestDumpAllTrees:
    def test_dump_all_trees(self, tamagotchi_repo, tmpdir_factory):
        """
        Only really a smoke test, checking that no errors occur, and that
        at least one file ends up as expected.
        """
        dump_dir = tmpdir_factory.mktemp("dump-all-trees")
        literategit.dump_all_trees.dump_all_trees(
            tamagotchi_repo,
            "start",
            "for-rendering",
            dump_dir)

        sample_file = (
            Path(dump_dir)
            / "commit-trees"
            / "6c"
            / "02bd6b238ed84550bd5cee4fd0a94d9f344da1"
            / "code.js"
        )

        with sample_file.open("rt") as f_in:
            sample_code = f_in.read()

        assert sample_code.startswith("$(document).ready")
