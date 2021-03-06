# -*- coding: utf-8 -*-

from pynfe.utils import etree, remover_acentos
import subprocess


class Assinatura(object):
    """Classe abstrata responsavel por definir os metodos e logica das classes
    de assinatura digital."""

    certificado = None
    senha = None

    def __init__(self, certificado, senha, autorizador=None):
        self.certificado = certificado
        self.senha = senha
        self.autorizador = autorizador

    def assinar(self, xml):
        """Efetua a assinatura da nota"""
        pass


class AssinaturaA1(Assinatura):
    """Classe responsavel por efetuar a assinatura do certificado
    digital no XML informado."""

    def assinar(self, xml, retorna_string=False):
        try:
            # No raiz do XML de saida
            tag = 'infNFe'  # tag que será assinada
            raiz = etree.Element('Signature', xmlns='http://www.w3.org/2000/09/xmldsig#')
            siginfo = etree.SubElement(raiz, 'SignedInfo')
            etree.SubElement(siginfo, 'CanonicalizationMethod', Algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315')
            etree.SubElement(siginfo, 'SignatureMethod', Algorithm='http://www.w3.org/2000/09/xmldsig#rsa-sha1')
            # Tenta achar a tag infNFe
            try:
                ref = etree.SubElement(siginfo, 'Reference', URI='#'+xml.findall('infNFe')[0].attrib['Id'])
            # Caso nao tenha a tag infNFe, procura a tag infEvento
            except IndexError:
                tag = 'infEvento'
                ref = etree.SubElement(siginfo, 'Reference', URI='#'+xml.findall('infEvento')[0].attrib['Id'])
            trans = etree.SubElement(ref, 'Transforms')
            etree.SubElement(trans, 'Transform', Algorithm='http://www.w3.org/2000/09/xmldsig#enveloped-signature')
            etree.SubElement(trans, 'Transform', Algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315')
            etree.SubElement(ref, 'DigestMethod', Algorithm='http://www.w3.org/2000/09/xmldsig#sha1')
            etree.SubElement(ref, 'DigestValue')
            etree.SubElement(raiz, 'SignatureValue')
            keyinfo = etree.SubElement(raiz, 'KeyInfo')
            etree.SubElement(keyinfo, 'X509Data')

            xml.append(raiz)

            # Escreve no arquivo depois de remover caracteres especiais e parse string
            with open('testes.xml', 'w') as arquivo:
                arquivo.write(remover_acentos(etree.tostring(xml, encoding="unicode", pretty_print=False)))

            subprocess.call(['xmlsec1', '--sign', '--pkcs12', self.certificado, '--pwd', self.senha, '--crypto', 'openssl', '--output', 'funfa.xml', '--id-attr:Id', tag, 'testes.xml'])
            xml = etree.parse('funfa.xml').getroot()

            if retorna_string:
                return etree.tostring(xml, encoding="unicode", pretty_print=False)
            else:
                return xml
        except Exception as e:
            raise e

    def assinarNfse(self, xml, retorna_string=True):
        "Assina NFS-e"
        try:
            # define variaveis de acordo com autorizador
            if self.autorizador == 'ginfes':
                xpath = './/ns2:InfRps'
                tag = 'InfRps'
            elif self.autorizador == 'betha':
                xpath = './/ns1:InfDeclaracaoPrestacaoServico'
                tag = 'InfDeclaracaoPrestacaoServico'
            else:
                raise Exception('Autorizador não encontrado!')

            xml = etree.fromstring(xml)
            # define namespaces, pega do proprio xml
            namespaces = xml.nsmap
            # No raiz do XML de saida
            raiz = etree.Element('Signature', xmlns='http://www.w3.org/2000/09/xmldsig#')
            siginfo = etree.SubElement(raiz, 'SignedInfo')
            etree.SubElement(siginfo, 'CanonicalizationMethod', Algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315')
            etree.SubElement(siginfo, 'SignatureMethod', Algorithm='http://www.w3.org/2000/09/xmldsig#rsa-sha1')
            # Tenta achar a tag
            ref = etree.SubElement(siginfo, 'Reference', URI='#' +
                                   xml.xpath(xpath, namespaces=namespaces)[0].attrib['Id'])
            trans = etree.SubElement(ref, 'Transforms')
            etree.SubElement(trans, 'Transform', Algorithm='http://www.w3.org/2000/09/xmldsig#enveloped-signature')
            etree.SubElement(trans, 'Transform', Algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315')
            etree.SubElement(ref, 'DigestMethod', Algorithm='http://www.w3.org/2000/09/xmldsig#sha1')
            etree.SubElement(ref, 'DigestValue')
            etree.SubElement(raiz, 'SignatureValue')
            keyinfo = etree.SubElement(raiz, 'KeyInfo')
            etree.SubElement(keyinfo, 'X509Data')

            rps = xml.xpath(xpath+'/..', namespaces=namespaces)[0]
            rps.append(raiz)

            # Escreve no arquivo depois de remover caracteres especiais e parse string
            with open('nfse.xml', 'w') as arquivo:
                texto = remover_acentos(etree.tostring(xml, encoding="unicode", pretty_print=False))
                # se for tag do Betha
                if tag == 'InfDeclaracaoPrestacaoServico':
                    texto = texto.replace('ns1:', '').replace(':ns1', '')
                arquivo.write(texto)

            subprocess.call(['xmlsec1', '--sign', '--pkcs12', self.certificado,
                             '--pwd', self.senha, '--crypto', 'openssl', '--output',
                             'nfse.xml', '--id-attr:Id', tag, 'nfse.xml'])

            if retorna_string:
                return open('nfse.xml', 'r').read()
            else:
                return etree.parse('nfse.xml').getroot()
        except Exception as e:
            raise e

    def assinarLote(self, xml, retorna_string=True):
        "Assina nfse e lote"
        try:
            xml = self.assinarNfse(xml, retorna_string=False)
            xpath = './/ns1:LoteRps'
            tag = 'LoteRps'
            # define namespaces, pega do proprio xml
            namespaces = xml.nsmap
            # No raiz do XML de saida
            raiz = etree.Element('Signature', xmlns='http://www.w3.org/2000/09/xmldsig#')
            siginfo = etree.SubElement(raiz, 'SignedInfo')
            etree.SubElement(siginfo, 'CanonicalizationMethod', Algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315')
            etree.SubElement(siginfo, 'SignatureMethod', Algorithm='http://www.w3.org/2000/09/xmldsig#rsa-sha1')
            # Tenta achar a tag
            ref = etree.SubElement(siginfo, 'Reference', URI='#' +
                                   xml.xpath(xpath, namespaces=namespaces)[0].attrib['Id'])
            trans = etree.SubElement(ref, 'Transforms')
            etree.SubElement(trans, 'Transform', Algorithm='http://www.w3.org/2000/09/xmldsig#enveloped-signature')
            etree.SubElement(trans, 'Transform', Algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315')
            etree.SubElement(ref, 'DigestMethod', Algorithm='http://www.w3.org/2000/09/xmldsig#sha1')
            etree.SubElement(ref, 'DigestValue')
            etree.SubElement(raiz, 'SignatureValue')
            keyinfo = etree.SubElement(raiz, 'KeyInfo')
            etree.SubElement(keyinfo, 'X509Data')

            # posiciona tag Signature antes do LoteRps para assinar
            base = xml.xpath(xpath+'/..', namespaces=namespaces)[0]
            base.insert(0, raiz)

            # Escreve no arquivo depois de remover caracteres especiais
            with open('nfse.xml', 'w') as arquivo:
                texto = remover_acentos(etree.tostring(xml, encoding="unicode", pretty_print=False))
                arquivo.write(texto)
            # assina lote
            subprocess.call(['xmlsec1', '--sign', '--pkcs12', self.certificado,
                             '--pwd', self.senha, '--crypto', 'openssl', '--output',
                             'nfse.xml', '--id-attr:Id', tag, 'nfse.xml'])

            # Reposiciona tag Signature apos LoteRps
            xml = etree.fromstring(open('nfse.xml', 'r').read())
            namespaces = xml.nsmap
            sig = xml.find('{http://www.w3.org/2000/09/xmldsig#}Signature')
            sig.getparent().remove(sig)
            xml.append(sig)

            if retorna_string:
                return etree.tostring(xml, encoding="unicode", pretty_print=False)
            else:
                return xml
        except Exception as e:
            raise e

    def assinarCancelar(self, xml, retorna_string=True):
        """ Método que assina o xml para cancelamento de NFS-e """
        try:
            if self.autorizador == 'ginfes':
                xpath = 'CancelarNfseEnvio'
                tag = 'CancelarNfseEnvio'
                namespaces = {'ns1': 'http://www.ginfes.com.br/servico_cancelar_nfse_envio', 'ns2':'http://www.ginfes.com.br/tipos'}
            elif self.autorizador == 'betha':
                xpath = '/CancelarNfseEnvio/ns1:Pedido'
                tag = 'InfPedidoCancelamento'
                namespaces = {'ns1': 'http://www.betha.com.br/e-nota-contribuinte-ws'}
            else:
                raise Exception('Autorizador não encontrado!')

            xml = etree.fromstring(xml)
            # No raiz do XML de saida
            raiz = etree.Element('Signature', xmlns='http://www.w3.org/2000/09/xmldsig#')
            siginfo = etree.SubElement(raiz, 'SignedInfo')
            etree.SubElement(siginfo, 'CanonicalizationMethod', Algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315')
            etree.SubElement(siginfo, 'SignatureMethod', Algorithm='http://www.w3.org/2000/09/xmldsig#rsa-sha1')
            # Tenta achar a tag informada no xpath
            if tag == 'InfPedidoCancelamento':
                ref = etree.SubElement(siginfo, 'Reference', URI='#'+xml.xpath('.//ns1:'+tag, namespaces=namespaces)[0].attrib['Id'])
            # ginfes não tem id no cancelamento v2
            else:
                ref = etree.SubElement(siginfo, 'Reference', URI='')
            trans = etree.SubElement(ref, 'Transforms')
            etree.SubElement(trans, 'Transform', Algorithm='http://www.w3.org/2000/09/xmldsig#enveloped-signature')
            etree.SubElement(trans, 'Transform', Algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315')
            etree.SubElement(ref, 'DigestMethod', Algorithm='http://www.w3.org/2000/09/xmldsig#sha1')
            etree.SubElement(ref, 'DigestValue')
            etree.SubElement(raiz, 'SignatureValue')
            keyinfo = etree.SubElement(raiz, 'KeyInfo')
            etree.SubElement(keyinfo, 'X509Data')

            if tag == 'InfPedidoCancelamento':
                xml = xml.xpath(xpath, namespaces=namespaces)[0]
            # ginfes só possui a tag root
            else:
               xml.append(raiz)

            # Escreve no arquivo depois de remover caracteres especiais e parse string
            with open('nfse.xml', 'w') as arquivo:
                arquivo.write(remover_acentos(etree.tostring(xml, encoding="unicode", pretty_print=False).replace('\n','')))

            subprocess.call(['xmlsec1', '--sign', '--pkcs12', self.certificado, '--pwd', self.senha, '--crypto', 'openssl', '--output', 'funfa.xml', '--id-attr:Id', tag, 'nfse.xml'])

            if retorna_string:
                return open('funfa.xml', 'r').read()
            else:
                return etree.parse('funfa.xml').getroot()
        except Exception as e:
            raise e

    def assinarConsulta(self, xml, retorna_string=True):
        try:
            xml = etree.fromstring(xml)
            # No raiz do XML de saida
            tag = 'ns1:ConsultarNfseEnvio'  # tag que será assinada
            raiz = etree.Element('Signature', xmlns='http://www.w3.org/2000/09/xmldsig#')
            siginfo = etree.SubElement(raiz, 'SignedInfo')
            etree.SubElement(siginfo, 'CanonicalizationMethod', Algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315')
            etree.SubElement(siginfo, 'SignatureMethod', Algorithm='http://www.w3.org/2000/09/xmldsig#rsa-sha1')
            # Consulta nao tem id
            ref = etree.SubElement(siginfo, 'Reference', URI='')

            trans = etree.SubElement(ref, 'Transforms')
            etree.SubElement(trans, 'Transform', Algorithm='http://www.w3.org/2000/09/xmldsig#enveloped-signature')
            etree.SubElement(trans, 'Transform', Algorithm='http://www.w3.org/TR/2001/REC-xml-c14n-20010315')
            etree.SubElement(ref, 'DigestMethod', Algorithm='http://www.w3.org/2000/09/xmldsig#sha1')
            etree.SubElement(ref, 'DigestValue')
            etree.SubElement(raiz, 'SignatureValue')
            keyinfo = etree.SubElement(raiz, 'KeyInfo')
            etree.SubElement(keyinfo, 'X509Data')

            consulta = xml.xpath('/ns1:ConsultarNfseEnvio', namespaces={'ns1': 'http://www.ginfes.com.br/servico_consultar_nfse_envio_v03.xsd', 'ns2':'http://www.ginfes.com.br/tipos_v03.xsd'})[0]
            consulta.append(raiz)

            # Escreve no arquivo depois de remover caracteres especiais e parse string
            with open('nfse.xml', 'w') as arquivo:
                arquivo.write(remover_acentos(etree.tostring(xml, encoding="unicode", pretty_print=False).replace('\n','')))

            subprocess.call(['xmlsec1', '--sign', '--pkcs12', self.certificado, '--pwd', self.senha, '--crypto', 'openssl', '--output', 'funfa.xml', '--id-attr:Id', tag, 'nfse.xml'])
            xml = etree.parse('funfa.xml').getroot()

            if retorna_string:
                return etree.tostring(xml, encoding="unicode", pretty_print=False)
            else:
                return xml
        except Exception as e:
            raise e
