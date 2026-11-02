from blog import create_app


def test_post_links_are_url_encoded(conn, tmp_path):
    conn.execute(
        "INSERT INTO posts (slug, title, published, tags, body) VALUES (?, ?, ?, ?, ?)",
        ("c# tips", "C# tips", "2026-11-02", "", "body\n"),
    )
    conn.commit()
    html = create_app(tmp_path / "blog.db").test_client().get("/").get_data(as_text=True)
    assert 'href="/posts/c%23%20tips"' in html
