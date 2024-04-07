# Copyright (C) 2016, 2019, 2024 Ben North and others; see COPYING
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
import importlib
import click
import literategit
from literategit._version import __version__
from literategit.cli.repo_for_path import repo_for_path


def render_(
    title, begin_commit, end_commit, create_url, results,
    *,
    _path=None,
    _print=print,
):
    """
    Write, to stdout, an HTML representation of the repo history starting
    from (but excluding) BEGIN_COMMIT and ending, inclusively, with
    END_COMMIT.

    The CREATE_URL argument should be in the form

        possibly.nested.package.object

    where 'object' within the importable 'possibly.nested.package' should
    have callable attributes 'result_url' and 'source_url'.  For example,
    'object' can be a class with the given 'staticmethod's.  For more
    details see the code (TemplateSuite).

    The TITLE argument provides the contents of the <title> and <h1>
    elements in the rendered output.
    """
    repo_path = _path or os.getcwd()
    repo = repo_for_path(repo_path)

    sections = literategit.list_from_range(repo,
                                           begin_commit,
                                           end_commit)

    import_name, obj_name = create_url.rsplit('.', 1)
    try:
        create_url_module = importlib.import_module(import_name)
    except ImportError:
        import sys
        sys.path.append(repo_path)
        create_url_module = importlib.import_module(import_name)

    create_url = getattr(create_url_module, obj_name)

    _print(literategit.render(sections, create_url, title, results))


@click.command
@click.argument("title")
@click.argument("begin_commit")
@click.argument("end_commit")
@click.argument("create_url")
@click.option(
    "--results/--no-results",
    default=True,
    help="whether to include 'results' links in output (default yes)"
)
def render(
    title, begin_commit, end_commit, create_url, results,
):
    render_(title, begin_commit, end_commit, create_url, results)
