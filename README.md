# 📄 PDF Editor

Editor de PDF desktop construído com Python, CustomTkinter e PyMuPDF.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Funcionalidades

- **Visualizar PDF** — Renderização de alta qualidade com zoom (Ctrl + scroll)
- **Painel de páginas** — Miniaturas navegáveis na barra lateral
- **Seleção retangular** — Selecione áreas do PDF com clique e arraste
- **Seleção livre** — Desenhe seleções à mão livre
- **Remover conteúdo** — Apague texto, imagens ou tabelas de áreas selecionadas
- **Inserir texto** — Adicione texto em qualquer posição da página
- **Reordenar páginas** — Mova páginas para cima ou para baixo
- **Excluir páginas** — Remova páginas indesejadas
- **Salvar PDF** — Exporte o PDF editado
- **Exportar para Word** — Converta para `.docx` preservando tabelas e formatação

## 📸 Screenshot

<p align="center">
  <img src="docs/screenshot.png" alt="PDF Editor Screenshot" width="800">
</p>

## 🚀 Instalação

### Pré-requisitos

- Python 3.10 ou superior

### Passos

```bash
# Clone o repositório
git clone https://github.com/rafaelmendoncadev/PDF-Editor.git
cd PDF-Editor

# Crie um ambiente virtual (recomendado)
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # Linux/macOS

# Instale as dependências
pip install -r requirements.txt
```

## ▶️ Uso

```bash
python main.py
```

A janela do editor abrirá. Use o botão **📂 Abrir PDF** para carregar um arquivo.

## 🛠 Tecnologias

| Biblioteca | Uso |
|---|---|
| [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) | Interface gráfica moderna |
| [PyMuPDF (fitz)](https://pymupdf.readthedocs.io/) | Leitura, renderização e manipulação de PDF |
| [Pillow](https://pillow.readthedocs.io/) | Processamento de imagens |
| [python-docx](https://python-docx.readthedocs.io/) | Exportação para Word (.docx) |

## 📁 Estrutura do Projeto

```
PDF Editor/
├── main.py                  # Ponto de entrada
├── requirements.txt         # Dependências
├── app/
│   ├── core/
│   │   ├── pdf_document.py      # Modelo do documento PDF
│   │   ├── pdf_renderer.py      # Renderização de páginas (pixmap → PIL)
│   │   ├── pdf_exporter.py      # Exportação / salvamento
│   │   ├── pdf_to_word.py       # Conversão PDF → Word
│   │   ├── content_remover.py   # Remoção de conteúdo por região
│   │   ├── content_inserter.py  # Inserção de texto
│   │   ├── selection_manager.py # Gerenciamento de seleções
│   │   └── edit_history.py      # Histórico de edições
│   └── ui/
│       ├── main_window.py       # Janela principal (mediador)
│       ├── toolbar.py           # Barra de ferramentas
│       ├── pdf_viewer.py        # Canvas de visualização com zoom
│       ├── page_panel.py        # Painel de miniaturas
│       └── dialogs/
│           ├── text_editor_dialog.py        # Diálogo de inserção de texto
│           └── selection_preview_dialog.py  # Diálogo de ação pós-seleção
└── docs/
    └── ...
```

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

