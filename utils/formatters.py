import re

def to_snake_case(texto: str) -> str:
    # Remove espaços laterais e substitui hífens por espaços
    texto = texto.strip().replace('-', ' ')
    
    # Insere underscore antes de letras maiúsculas (caso camelCase ou PascalCase)
    texto = re.sub(r'([a-z])([A-Z])', r'\1_\2', texto)
    
    # Substitui espaços e outros caracteres não alfanuméricos por underscore
    texto = re.sub(r'[\s]+', '_', texto)
    texto = re.sub(r'[^\w_]', '', texto)
    
    # Converte tudo para minúsculas
    return texto.lower()
