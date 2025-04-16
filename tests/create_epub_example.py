#!/usr/bin/env python3
# create_epub_example.py

"""
Exemplo de como criar um arquivo EPUB do zero usando a biblioteca bkepub.
Este script demonstra a criação de um livro simples com alguns capítulos,
uma folha de estilo, imagens e uma estrutura de navegação.
"""

import os
from bkepub import (
    EpubBuilder,
    ROLE_AUTHOR,
    ROLE_EDITOR,
    LANDMARK_COVER,
    LANDMARK_TOC,
    LANDMARK_BODMATTER
)


def main():
    # Criar uma nova instância do construtor de EPUB
    epub = EpubBuilder()

    # Definir metadados básicos
    epub.set_title("Meu Primeiro eBook com bkepub")
    epub.set_language("pt-BR")
    epub.add_creator("Autor Exemplo", ROLE_AUTHOR, "Exemplo, Autor")
    epub.add_creator("Editor Exemplo", ROLE_EDITOR)

    # Adicionar uma folha de estilo CSS
    css_content = """
    body {
        font-family: serif;
        margin: 5%;
        text-align: justify;
    }
    h1, h2 {
        text-align: center;
        color: #333;
    }
    .cover {
        text-align: center;
        page-break-after: always;
    }
    .cover img {
        max-width: 100%;
    }
    .titlepage {
        text-align: center;
        margin-top: 20%;
    }
    """
    css = epub.add_css("main.css", css_content, item_id="main-css")


    # Adicionar a imagem de capa
    with open("images/cover.jpg", "rb") as img_file:
        cover_img_content = img_file.read()
        cover_img = epub.add_image("cover.jpg", cover_img_content)
        epub.set_cover_image(cover_img)

    # Criar uma página HTML para a capa (com CSS vinculado)
    cover_html = """
    <div class="cover">
        <img src="Images/cover.jpg" alt="Capa do livro" />
        <h1>Meu Primeiro eBook</h1>
        <h2>Autor Exemplo</h2>
    </div>
    """
    cover_page = epub.add_xhtml("cover.xhtml", cover_html, "cover", "Capa", css_ids=["main-css"])

    # Adicionar página de título (com CSS vinculado)
    title_html = """
    <div class="titlepage">
        <h1>Meu Primeiro eBook com bkepub</h1>
        <h2>Autor Exemplo</h2>
        <p>Publicado por: Exemplo Editora</p>
        <p>© 2025</p>
    </div>
    """
    title_page = epub.add_xhtml("titlepage.xhtml", title_html, "titlepage", "Página de Título", css_ids=["main-css"])


    # Adicionar capítulos (com CSS vinculado)
    chapter1_content = """
    <h1 id="ch1">Capítulo 1</h1>
    <p>Este é o primeiro capítulo do nosso livro de exemplo.</p>
    <p>Podemos usar este texto para demonstrar como formatar conteúdo para e-readers.</p>
    <p>O conteúdo pode incluir <strong>formatação</strong>, <em>estilos</em> e muito mais.</p>

    <h2 id="ch1-sec1">Seção 1.1</h2>
    <p>Esta é uma subseção do capítulo 1.</p>

    <h2 id="ch1-sec2">Seção 1.2</h2>
    <p>Esta é outra subseção do capítulo 1.</p>
    """
    chapter1 = epub.add_xhtml("chapter1.xhtml", chapter1_content, "chapter1", "Capítulo 1", css_ids=["main-css"])

    chapter2_content = """
    <h1 id="ch2">Capítulo 2</h1>
    <p>Este é o segundo capítulo do nosso livro.</p>
    <p>Podemos continuar adicionando tantos capítulos quanto necessário.</p>

    <h2 id="ch2-sec1">Seção 2.1</h2>
    <p>Esta é uma subseção do capítulo 2.</p>

    <h2 id="ch2-sec2">Seção 2.2</h2>
    <p>Esta é outra subseção do capítulo 2.</p>
    """
    chapter2 = epub.add_xhtml("chapter2.xhtml", chapter2_content, "chapter2", "Capítulo 2", css_ids=["main-css"])

    # Verificar se o pacote Python markdown está instalado
    try:
        import markdown
    except ImportError:
        print("AVISO: Pacote 'markdown' não está instalado. Instalando...")
        import subprocess
        subprocess.check_call(["pip", "install", "markdown"])
        print("Pacote 'markdown' instalado com sucesso!")

    # Adicionar conteúdo Markdown (convertido automaticamente para XHTML)
    markdown_content = """
    # Apêndice

    Este é um exemplo de conteúdo **Markdown** que será automaticamente convertido para XHTML.

    ## Lista de recursos

    * Item 1
    * Item 2
    * Item 3

    ## Tabela de exemplo

    | Coluna 1 | Coluna 2 |
    |----------|----------|
    | Dado 1   | Dado 2   |
    | Dado 3   | Dado 4   |

    """

    # Em vez de usar add_markdown, vamos converter manualmente para XHTML
    # como alternativa caso a função add_markdown não esteja funcionando
    try:
        appendix = epub.add_markdown("appendix.xhtml", markdown_content, "appendix", "Apêndice")
        appendix_added = True
    except Exception as e:
        print(f"Erro ao usar add_markdown: {e}")
        print("Usando método alternativo para converter Markdown...")

        # Conversão manual de Markdown para HTML
        import markdown
        html_content = markdown.markdown(markdown_content, extensions=['extra', 'tables'])

        # Adicionar o conteúdo como XHTML normal
        appendix = epub.add_xhtml("appendix.xhtml", html_content, "appendix", "Apêndice", css_ids=["main-css"])
        appendix_added = True

    # Definir a ordem de leitura (spine)
    epub.add_spine_item(cover_page)
    epub.add_spine_item(title_page)
    epub.add_spine_item(chapter1)
    epub.add_spine_item(chapter2)
    if appendix_added:
        epub.add_spine_item(appendix)

    # Definir a estrutura do sumário (TOC)
    toc_entries = [
        {'label': 'Capa', 'href': cover_page.href},
        {'label': 'Página de Título', 'href': title_page.href},
        {'label': 'Capítulo 1', 'href': chapter1.href, 'children': [
            {'label': 'Seção 1.1', 'href': f"{chapter1.href}#ch1-sec1"},
            {'label': 'Seção 1.2', 'href': f"{chapter1.href}#ch1-sec2"}
        ]},
        {'label': 'Capítulo 2', 'href': chapter2.href, 'children': [
            {'label': 'Seção 2.1', 'href': f"{chapter2.href}#ch2-sec1"},
            {'label': 'Seção 2.2', 'href': f"{chapter2.href}#ch2-sec2"}
        ]}
    ]

    # Adicionar o apêndice à estrutura TOC se foi adicionado com sucesso
    if appendix_added:
        toc_entries.append({'label': 'Apêndice', 'href': appendix.href})

    epub.set_toc(toc_entries)

    # Adicionar marcos de navegação (landmarks)
    epub.add_landmark("Capa", cover_page.href, LANDMARK_COVER)
    epub.add_landmark("Início", chapter1.href, LANDMARK_BODMATTER)

    # Salvar o EPUB
    output_path = "meu_primeiro_ebook.epub"
    print(f"Salvando EPUB em: {output_path}")
    try:
        epub.save(output_path)
        print(f"EPUB criado com sucesso: {output_path}")
    except Exception as e:
        print(f"Erro ao salvar o EPUB: {e}")


if __name__ == "__main__":
    main()