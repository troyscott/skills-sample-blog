---
name: writing-a-post
description: Draft, add or edit a blog post as a markdown file in posts/ and load it into the site. Use when the user asks to write, draft, add, publish or edit a blog post, or to turn notes into a post.
---

# Writing a post

A post is one file, `posts/YYYY-MM-DD-short-slug.md`. The filename without `.md` is the URL: `/posts/YYYY-MM-DD-short-slug`.

~~~markdown
---
title: Why we moved the blog to SQLite
published: 2026-11-02
tags: databases, ops
---
The body, in markdown.
~~~

`title` and `published` (YYYY-MM-DD) are required. `tags` is optional, comma-separated.

How to write it:

- If the audience or the one point of the post isn't clear, ask before drafting.
- Keep the user's facts and voice. Don't add claims, numbers or quotes they didn't give you; mark gaps as `TODO:` for them to fill.
- Lead with the point. One idea per post.
- Don't rename an existing post's file: it changes its URL and breaks links.

Check it loads, then show the user the page:

~~~bash
python -m blog sync
~~~

If sync fails it names the file and the problem, and loads nothing. Fix the front matter and run it again.
