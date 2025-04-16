from bkepub import EpubBuilder

# Criar um novo EPUB
epub = EpubBuilder()

# Adicionar título e outros metadados
epub.set_title("Meu Livro")
epub.set_language("pt-BR")

# Adicionar conteúdo
epub.add_xhtml("chapter1.xhtml", "<h1>Capítulo 1</h1><p>Conteúdo...</p>")
epub.add_xhtml("chapter2.xhtml", "<h1>Capítulo 2</h1><h2>Seção 2.1</h2><p>Conteúdo...</p>")

# Adicionar itens ao spine
epub.add_spine_item("html-1")
epub.add_spine_item("html-2")

# Gerar TOC automaticamente a partir dos cabeçalhos H1-H3
epub.generate_toc_from_spine(max_heading_level=3)

# Salvar o EPUB
epub.save("meu_livro.epub")