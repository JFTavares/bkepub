# 2. Add Metadata
book.add_metadata('dc', 'A BkEpub Showcase', tag='title', attributes={'title-type': 'subtitle'}) # Example subtitle meta
book.add_creator("Alice Author", role=ROLE_AUTHOR, file_as="Author, Alice", creator_id="creator-alice")
book.add_creator("Bob Editor", role=ROLE_EDITOR, file_as="Editor, Bob", creator_id="creator-bob")
book.add_creator("Charlie Illustrator", role=ROLE_ILLUSTRATOR, file_as="Illustrator, Charlie", creator_id="creator-charlie")
book.add_metadata('dc', 'BkEpub Publishing', tag='publisher')
book.add_metadata('dc', datetime.date.today().strftime('%Y-%m-%d'), tag='date') # Publication date
book.add_metadata('dc', 'EPUB, Python, Programming, Example', tag='subject')
book.add_metadata('dc', 'An example demonstrating advanced features of the BkEpub library.', tag='description')
book.add_metadata('dc', 'Copyright (c) 2023 Your Name/Org. All rights reserved.', tag='rights')
book.add_metadata('meta', 'cover-image', property_attr='bkepub-meta', meta_id='meta-cover-ref') # Example custom meta


# 3. Add Items (Content, Styles, Images, Fonts, JS)

# Cover Image
item_cover_img = None
if COVER_IMG_PATH and os.path.exists(COVER_IMG_PATH):
     with open(COVER_IMG_PATH, "rb") as f:
         cover_content = f.read()
     item_cover_img = book.add_image(
         file_name=f"{IMAGE_DIR}/cover.png", # Relative to OEBPS dir
         content=cover_content,
         item_id="cover-image" # Explicit ID
     )
     book.set_cover(item_cover_img.id)
     # Also refine the custom meta tag example
     book.add_meta('meta', item_cover_img.id, property_attr='refines', refines='#meta-cover-ref')

else:
     print("Warning: Cover image file not found or PIL missing. Skipping cover.")


# Stylesheets
item_css_main = book.add_stylesheet("css/style.css", main_css_content, item_id="main-style")
item_css_font = book.add_stylesheet("css/fonts.css", font_css_content, item_id="font-style")

# JavaScript
item_js = book.add_javascript("js/interactive.js", js_content, item_id="interactivity")

# Font
item_font = None
if os.path.exists(FONT_PATH):
    with open(FONT_PATH, "rb") as f:
        font_content = f.read()
    item_font = book.add_font(
        file_name=f"{FONT_DIR}/DejaVuSerif-Regular.ttf", # Relative path
        content=font_content,
        item_id="font-dejavu"
    )
else:
    print(f"Warning: Font file {FONT_PATH} not found. Skipping font.")


# Content Documents (Order matters for default spine)
# Title page (not typically in linear spine, added manually later if needed)
item_title = book.add_html_content(
    file_name="title.xhtml",
    content=title_page_html,
    nav_title="Title Page", # Title for TOC/NCX
    item_id="titlepage",
    add_to_spine=False # Don't add to linear reading order by default
)

# Chapter 1 (from Markdown)
item_chap1 = book.add_markdown_content(
    file_name="chap1.xhtml",
    markdown_content=chap1_md,
    nav_title="Chapter 1: Setup",
    item_id="chap1"
    # Automatically added to spine=True by default
)

# Chapter 2 (from pre-built XHTML)
item_chap2 = book.add_item(
     HtmlContentItem(
         item_id="chap2",
         file_name="chap2.xhtml",
         content=chap2_html_content.encode('utf-8'), # Ensure bytes
         nav_title="Chapter 2: Advanced",
         language=BOOK_LANG # Can specify lang per file
     )
)
# Explicitly add to spine (since add_item doesn't auto-add)
book.add_spine_item(item_chap2.id, linear=True)

# Important: Mark Chapter 2 as scripted because it includes JS
item_chap2.properties.add('scripted') # Add 'scripted' property


# 4. Build Table of Contents (Structured)
# BkEpub's add_toc_entry currently appends. For nesting, build the structure manually.
# (Future improvement: add_toc_entry could take a parent_id)
# Let's build the structure and assign it directly (accessing internal list - use with caution)
toc_structure = [
    {'label': item_title.nav_title, 'href': item_title.href, 'children': []},
    {'label': item_chap1.nav_title, 'href': item_chap1.href, 'children': [
        {'label': 'Metadata Section', 'href': f'{item_chap1.href}#metadata-is-key', 'children': []}, # Example fragment link
        {'label': 'Creators Section', 'href': f'{item_chap1.href}#adding-creators', 'children': []},
    ]},
    {'label': item_chap2.nav_title, 'href': item_chap2.href, 'children': [
         {'label': 'Fonts Subsection', 'href': f'{item_chap2.href}#fonts', 'children': []},
         {'label': 'JavaScript Subsection', 'href': f'{item_chap2.href}#scripting', 'children': []},
    ]},
]
book._toc_entries = toc_structure # Assign the manually built structure


# 5. Define Landmarks
if item_cover_img:
    # Find the HTML page visually representing the cover (often the title page or a dedicated cover.xhtml)
    # Here, let's assume the title page serves this role for the landmark link.
    book.add_landmark("Cover", item_title.href, LANDMARK_COVER)
book.add_landmark("Table of Contents", f"{book.nav_file_name}#toc", LANDMARK_TOC) # Link to generated nav
book.add_landmark("Begin Reading", item_chap1.href, LANDMARK_BODMATTER)
book.add_landmark("Title Page", item_title.href, LANDMARK_TITLEPAGE)


# 6. Include NCX for compatibility
book.include_ncx = True

# 7. Save the EPUB
print(f"Attempting to save EPUB to: {OUTPUT_FILENAME}")
book.save(OUTPUT_FILENAME)
print("-" * 30)
print(f"Successfully created complex EPUB: {OUTPUT_FILENAME}")
print(f"Identifier: {book.identifier}")
print(f"Content Directory: {book.oebps_dir}")
print(f"OPF File: {book.opf_file_name}")
print("-" * 30)
print("Note: Validate this EPUB using an external tool like epubcheck.")