from bkepub import EpubBuilder, EpubParseError

try:
    # Load the book
    loaded_book = EpubBuilder.load("my_awesome_book.epub")

    # Inspect properties
    print(f"Title: {loaded_book.metadata.find_dc('dc:title')}")
    print(f"Language: {loaded_book.metadata.find_dc('dc:language')}")
    print(f"Identifier: {loaded_book._book_id_ref}") # Access internal attribute for package ID ref
    print("\nManifest Items:")
    for item_id, item in loaded_book._manifest_items.items():
         print(f"- {item_id}: {item.href} ({item.media_type})")

    print("\nSpine Order:")
    for spine_ref in loaded_book.get_spine():
        print(f"- ID: {spine_ref['idref']}, Linear: {spine_ref['linear']}")

    print("\nTOC Entries:")
    def print_toc(entries, indent=0):
        for entry in entries:
            print(f"{'  ' * indent}- {entry['label']} -> {entry['href']}")
            if entry.get('children'):
                print_toc(entry['children'], indent + 1)
    print_toc(loaded_book.get_toc())

    print("\nLandmarks:")
    for landmark in loaded_book.get_landmarks():
        print(f"- {landmark['label']} ({landmark['type']}) -> {landmark['href']}")


    # Example Modification: Add a new metadata entry
    loaded_book.add_metadata('dc', 'Subject Example', tag='subject')

    # Save the modified book (to a different file)
    # loaded_book.save("my_awesome_book_modified.epub")

except EpubParseError as e:
    print(f"Error loading EPUB: {e}")
except FileNotFoundError:
    print("Error: EPUB file not found.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")