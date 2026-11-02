import pytest

from blog.posts import PostError, parse_post, sync

GOOD = "---\ntitle: Hello\npublished: 2026-11-02\ntags: meta\n---\nBody text.\n"


def write(tmp_path, name, text):
    path = tmp_path / name
    path.write_text(text)
    return path


def test_parse_reads_front_matter_and_slug(tmp_path):
    post = parse_post(write(tmp_path, "2026-11-02-hello.md", GOOD))
    assert (post.slug, post.title, post.published, post.tags) == (
        "2026-11-02-hello", "Hello", "2026-11-02", "meta",
    )
    assert post.body == "Body text.\n"


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("no front matter", "must start with"),
        ("---\ntitle: x\n", "no closing"),
        ("---\npublished: 2026-11-02\n---\nbody", "missing title"),
        ("---\ntitle: x\npublished: Nov 2\n---\nbody", "YYYY-MM-DD"),
    ],
)
def test_bad_posts_name_the_file_and_the_problem(tmp_path, text, message):
    with pytest.raises(PostError, match=message) as err:
        parse_post(write(tmp_path, "bad.md", text))
    assert "bad.md" in str(err.value)


def test_closing_line_without_trailing_newline_still_closes(tmp_path):
    post = parse_post(write(tmp_path, "a.md", "---\ntitle: a\npublished: 2026-11-02\n---"))
    assert (post.title, post.body) == ("a", "\n")


def test_sync_names_a_missing_or_empty_folder(conn, tmp_path):
    with pytest.raises(PostError, match="posts folder not found"):
        sync(conn, tmp_path / "post")
    (tmp_path / "empty").mkdir()
    with pytest.raises(PostError, match="no .md files"):
        sync(conn, tmp_path / "empty")


def test_sync_deletes_a_post_whose_file_is_gone(conn, tmp_path):
    write(tmp_path, "a.md", GOOD)
    gone = write(tmp_path, "b.md", GOOD)
    assert sync(conn, tmp_path) == 2
    gone.unlink()
    assert sync(conn, tmp_path) == 1
    assert [r[0] for r in conn.execute("SELECT slug FROM posts")] == ["a"]


def test_sync_is_all_or_nothing(conn, tmp_path):
    write(tmp_path, "a.md", GOOD)
    write(tmp_path, "b.md", "no front matter")
    with pytest.raises(PostError):
        sync(conn, tmp_path)
    assert conn.execute("SELECT count(*) FROM posts").fetchone()[0] == 0


def test_sync_updates_an_existing_post(conn, tmp_path):
    path = write(tmp_path, "a.md", GOOD)
    sync(conn, tmp_path)
    path.write_text(GOOD.replace("Hello", "Hello again"))
    assert sync(conn, tmp_path) == 1
    assert conn.execute("SELECT title FROM posts").fetchone()[0] == "Hello again"
