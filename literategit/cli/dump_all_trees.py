# Copyright (C) 2016 Ben North
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
import click
import literategit.dump_all_trees
from literategit._version import __version__
from literategit.cli.repo_for_path import repo_for_path


@click.command
@click.argument("output_root")
@click.argument("rev1")
@click.argument("rev2")
def dump_all_trees(output_root, rev1, rev2):
    """
    Write, to OUTPUT_ROOT, a collection of files which represent snapshots
    of all commits reachable from REV2 but not reachable from REV1.

    The newly-created output directory contains two directories:

        blobs/ --- Contains one file per blob reachable from any commit in
            REV1..REV2.  Each blob resides in a directory named by the first
            two characters of the blob's SHA1.  The remaining 38 characters
            of the SHA1 give the filename within that directory.

        commit-trees/ --- Contains one directory per commit, in the same
            2/38 format as the blobs.  Each commit's directory contains the
            files and directories making up the tree corresponding to that
            commit.  (Files are hard links to the appropriate blob within
            the blobs directory; directories are real directories.)
    """
    repo = repo_for_path(os.getcwd())
    literategit.dump_all_trees.dump_all_trees(repo,
                                              rev1, rev2,
                                              output_root)
