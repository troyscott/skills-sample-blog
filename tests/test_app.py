from blog import create_app
from blog.posts import sync


def test_index_lists_posts_and_post_page_renders(conn, tmp_path):
    posts = tmp_path / "posts"
    posts.mkdir()
    (posts / "2026-11-02-hello.md").write_text(
        "---\ntitle: Hello\npublished: 2026-11-02\n---\nSome **bold** text.\n"
    )
    sync(conn, posts)
    client = create_app(tmp_path / "blog.db").test_client()
    assert b'href="/posts/2026-11-02-hello"' in client.get("/").data
    assert b"<strong>bold</strong>" in client.get("/posts/2026-11-02-hello").data


def test_unknown_post_is_404(conn, tmp_path):
    client = create_app(tmp_path / "blog.db").test_client()
    assert client.get("/posts/nope").status_code == 404
