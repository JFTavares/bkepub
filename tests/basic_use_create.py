from bkepub import EpubBuilder, ROLE_AUTHOR, LANDMARK_COVER, LANDMARK_TOC





# 1. Create a new builder instance
book = EpubBuilder(
    title="The Adventures of BkEpub",
    language="en",
    identifier="urn:uuid:fmagic-wand-uuid-12345"
)
book.add_creator("Awesome Author", role=ROLE_AUTHOR, file_as="Author, Awesome")
book.add_metadata('dc', 'My Cool Publisher', tag='publisher')

# 2. Add content
# From XHTML string (auto-wrapped)
chap1_html = "<h1>Chapter 1</h1><p>It was a dark and stormy night...</p>"
item_chap1 = book.add_html_content(
    nav_title="The Beginning",
    file_name="chap1.xhtml",
    content=chap1_html
) # Automatically added to spine

# From Markdown string
chap2_md = """
## Chapter 2: The Journey

With the **map** in hand, our hero ventured forth.

* Item 1
* Item 2

> A quote about adventure.
"""
item_chap2 = book.add_markdown_content(
    nav_title="The Journey",
    file_name="chap2.xhtml",
    markdown_content=chap2_md
) # Also added to spine

# 3. Add a stylesheet
css_content = "body { font-family: 'Arial', sans-serif; } h1, h2 { color: navy; }"
item_css = book.add_stylesheet("style.css", css_content)
# Remember to link the CSS in your HTML files (e.g., within wrap_html_fragment or manually)

# 4. Add an image and set it as cover
try:
    with open("images.capa.jpg", "rb") as f:
        cover_content = f.read()
    item_cover_img = book.add_image("cover.jpg", cover_content, item_id="cover-img")
    book.set_cover(item_cover_img.id) # Designate the image item as cover
except FileNotFoundError:
    print("Warning: Cover image not found, skipping.")
    item_cover_img = None


# 5. Build Table of Contents (use item hrefs)
toc_chap1 = book.add_toc_entry(item_chap1.nav_title, item_chap1.href)
# Add a child entry (example)
# book.add_toc_entry("Section 1.1", f"{item_chap1.href}#section1", children=[]) # Assuming parent exists or use structure
book.add_toc_entry(item_chap2.nav_title, item_chap2.href)

# 6. Add Landmarks
if item_cover_img:
    book.add_landmark("Cover", item_cover_img.href, LANDMARK_COVER)
book.add_landmark("Table of Contents", f"{book.nav_file_name}#toc", LANDMARK_TOC) # Link to generated nav

# 7. (Optional) Include EPUB 2 NCX
book.include_ncx = True

# 8. Save the EPUB
try:
    book.save("my_awesome_book.epub")
    print("Ebook created successfully!")
except Exception as e:
    print(f"Error creating ebook: {e}")