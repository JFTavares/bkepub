#!/usr/bin/env python3
# load_epub_example.py



import os
import sys
from bkepub import load, EpubBuilder, HtmlContentItem


def print_epub_info(epub):
    """Imprime informações sobre o EPUB carregado."""
    print("=== Informações do EPUB ===")

    # Metadados
    title = epub.metadata.find_dc('dc:title')
    language = epub.metadata.find_dc('dc:language')
    identifiers = epub.metadata.find_all_dc('dc:identifier')

    print(f"Título: {title}")
    print(f"Idioma: {language}")
    print("Identificadores:")
    for id_text, id_attrs in identifiers:
        id_type = id_attrs.get('scheme', 'N/A')
        print(f"  - {id_text} (Tipo: {id_type})")

    # Criadores/Autores
    creators = epub.metadata.find_all_dc('dc:creator')
    if creators:
        print("Criadores:")
        for creator_name, creator_attrs in creators:
            print(f"  - {creator_name}")

    # Itens do manifesto
    manifest_items = epub.get_manifest_items()
    print(f"\nItens no manifesto: {len(manifest_items)}")

    by_type = {}
    for item in manifest_items:
        media_type = item.media_type
        if media_type not in by_type:
            by_type[media_type] = []
        by_type[media_type].append(item)

    for media_type, items in by_type.items():
        print(f"  - {media_type}: {len(items)} itens")

    # Estrutura do TOC
    print("\nEstrutura do Sumário (TOC):")

    def print_toc_entry(entry, level=0):
        indent = "  " * level
        print(f"{indent}- {entry['label']} ({entry['href']})")
        for child in entry.get('children', []):
            print_toc_entry(child, level + 1)

    for entry in epub._toc_entries:
        print_toc_entry(entry)

    # Ordem de leitura (spine)
    spine_items = epub.get_spine_items()
    print(f"\nOrdem de leitura (spine): {len(spine_items)} itens")
    for i, item in enumerate(spine_items):
        print(f"  {i + 1}. {item.id} - {item.href}")

    # Marcos (landmarks)
    if epub._landmarks:
        print("\nMarcos (landmarks):")
        for landmark in epub._landmarks:
            print(f"  - {landmark['label']} ({landmark['type']}): {landmark['href']}")


def modify_epub(epub, output_path):

    print("\n=== Modificando o EPUB ===")

    # 1. Adicionar um novo capítulo
    print("Adicionando um novo capítulo...")
    new_chapter_content = """
    <h1 id="new-chapter">Capítulo Adicional</h1>
    <p>Este é um novo capítulo que foi adicionado ao EPUB existente.</p>
    <p>Demonstra como podemos modificar um EPUB carregado e salvá-lo novamente.</p>

    <h2 id="new-section-1">Seção Adicional 1</h2>
    <p>Uma subseção do novo capítulo.</p>

    <h2 id="new-section-2">Seção Adicional 2</h2>
    <p>Outra subseção do novo capítulo.</p>
    """
    new_chapter = epub.add_xhtml("new_chapter.xhtml", new_chapter_content, "new_chapter", "Capítulo Adicional")

    # 2. Adicionar o novo capítulo ao spine (fim do livro)
    print("Adicionando novo capítulo à ordem de leitura (spine)...")
    epub.add_spine_item(new_chapter)

    # 3. Atualizar o sumário (TOC) para incluir o novo capítulo
    print("Atualizando o sumário (TOC)...")
    # Primeiro, fazemos uma cópia do TOC existente
    toc_entries = epub._toc_entries.copy()

    # Adicionamos uma nova entrada para o novo capítulo
    new_entry = {
        'label': 'Capítulo Adicional',
        'href': new_chapter.href,
        'children': [
            {'label': 'Seção Adicional 1', 'href': f"{new_chapter.href}#new-section-1"},
            {'label': 'Seção Adicional 2', 'href': f"{new_chapter.href}#new-section-2"}
        ]
    }
    toc_entries.append(new_entry)

    # Atualizamos o TOC
    epub.set_toc(toc_entries)

    # 4. Modificar um capítulo existente (por exemplo, o primeiro capítulo)
    print("Modificando um capítulo existente...")
    try:
        # Obtém o primeiro item de conteúdo HTML no spine
        html_items = [item for item in epub.get_spine_items() if isinstance(item, HtmlContentItem)]
        if html_items:
            first_chapter = html_items[0]

            # Decodificar o conteúdo atual
            current_content = first_chapter.content.decode('utf-8')

            # Adicionar um parágrafo no início
            modified_content = current_content.replace('<body>', """<body>
            <div class="modified-notice" style="color: red; text-align: center;">
                <p><strong>Este capítulo foi modificado!</strong></p>
            </div>
            """)

            # Atualizar o conteúdo
            first_chapter.content = modified_content.encode('utf-8')
            print(f"Modificado o capítulo: {first_chapter.href}")
        else:
            print("Nenhum capítulo HTML encontrado para modificar.")
    except Exception as e:
        print(f"Erro ao modificar capítulo existente: {e}")

    # 5. Atualizar metadados
    print("Atualizando metadados...")
    original_title = epub.metadata.find_dc('dc:title') or "Livro"
    epub.set_title(f"{original_title} (Modificado)")

    # 6. Salvar o EPUB modificado
    print(f"Salvando EPUB modificado em: {output_path}")
    epub.save(output_path)
    print(f"EPUB modificado salvo com sucesso: {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python load_epub_example.py [caminho_para_epub]")
        sys.exit(1)

    input_path = sys.argv[1]
    if not os.path.exists(input_path):
        print(f"Erro: O arquivo '{input_path}' não existe.")
        sys.exit(1)

    try:
        # Carregar o EPUB existente
        print(f"Carregando EPUB: {input_path}")
        epub = load(input_path)

        # Imprimir informações sobre o EPUB
        print_epub_info(epub)

        # Modificar o EPUB e salvar como novo arquivo
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = f"{base_name}_modificado.epub"
        modify_epub(epub, output_path)

    except Exception as e:
        print(f"Erro ao processar o EPUB: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()