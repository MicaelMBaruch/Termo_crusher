import re
from operator import itemgetter
from selenium.webdriver.common.keys import Keys


class JogadorVirtual:
    # inicializa termo crusher
    def __init__(self, navegador, palavras_termo, frequencia_letras_posicao):
        self.navegador = navegador
        self.navegador.get('https://term.ooo/')
        self.palavras_termo = palavras_termo
        self.frequencia_letras_posicao = frequencia_letras_posicao
        self.alfabeto = '[abcdefghijklmnopqrstuvwxyz]'
        self.letras_validas_posicao = [self.alfabeto, self.alfabeto, self.alfabeto, self.alfabeto, self.alfabeto]

    # letras globalmente validas e invalidas
        self.letras_invalidas = ''
        self.letras_existem = ''

    def melhores_palavras(self):
        palavras_possiveis = []
        for palavra in self.palavras_termo:
            if re.search(''.join(self.letras_validas_posicao), palavra):
                palavras_possiveis.append(palavra)
        chance = {}
        for palavra in palavras_possiveis:
            chance_palavra = 0
            for posicao, letra in enumerate(palavra):
                frequencia_letra = self.frequencia_letras_posicao[posicao][letra] 
                chance_letra = frequencia_letra/len(self.palavras_termo) #probabilidade da letra
                if letra in self.letras_existem:
                    chance_letra *= 80
                chance_letra /= len(re.findall(letra, palavra))
                chance_palavra += chance_letra 
            chance[palavra] = chance_palavra
        return sorted(chance.items(), key=itemgetter(1), reverse= True)

    def atualiza_validas_posicao(self, posicao_letra, letra_invalida):
        self.letras_validas_posicao[posicao_letra] = self.letras_validas_posicao[posicao_letra].replace(letra_invalida.lower(), '')

    def atualiza_validas_global(self):
        for letra_invalida in self.letras_invalidas:
            for posicao in range(len(self.letras_validas_posicao)):
                self.atualiza_validas_posicao(posicao, letra_invalida)

    def atualiza_palavras_possiveis(self, posicao, letra, feedback):
        if 'em outro local' in feedback:
            # letras invalidas em posições específicas
            self.atualiza_validas_posicao(posicao, letra)
            self.letras_existem += letra

        # Sabe letra e posição
        if 'correta' in feedback:
            self.letras_validas_posicao[posicao] = letra
        
        if 'errada' in feedback and letra not in self.letras_existem and letra not in self.letras_invalidas:
            self.letras_invalidas += letra

    def faz_melhor_chute(self, tentativa_atual):
        self.atualiza_validas_global()
        melhor_chute = self.melhores_palavras()[0][0] 
        termo_board = self.navegador.find_element_by_xpath('//*[@id="board0"]') 
        shadow_root_board = f'return arguments[0].shadowRoot.querySelector(\'wc-row[termo-row="{tentativa_atual}"]\');' 
        linha_atual = self.navegador.execute_script(shadow_root_board, termo_board)
        linha_atual.send_keys(melhor_chute)
        linha_atual.send_keys(Keys.ENTER)

    def recebe_feedback(self, tentativa_atual):
        padrao = r'letra "([^"]*)"\s+([^"]*)'
        letras_na_linha = ['', '', '', '', '']
        termo_board = self.navegador.find_element_by_xpath('//*[@id="board0"]') 
        shadow_root_board = f'return arguments[0].shadowRoot.querySelector(\'wc-row[termo-row="{tentativa_atual}"]\');' 
        linha_atual = self.navegador.execute_script(shadow_root_board, termo_board)
        for posicao_letra in range(len(letras_na_linha)):        
            shadow_root_line = f'return arguments[0].shadowRoot.querySelector(\'[lid="{posicao_letra}"][termo-row="{tentativa_atual}"][termo-pos="{posicao_letra}"]\');'
            letras_na_linha[posicao_letra] = self.navegador.execute_script(shadow_root_line, linha_atual)
            status = letras_na_linha[posicao_letra].get_attribute('aria-label')
            # Encontre todas as correspondências
            correspondencias = re.search(padrao, status)
            # Verifique se houve correspondência e obtenha a palavra
            if correspondencias:
                letra = correspondencias.group(1).lower()
                feedback = correspondencias.group(2)
                self.atualiza_palavras_possiveis(posicao_letra, letra, feedback)
            else:
                print("Nenhuma correspondência encontrada.")

        