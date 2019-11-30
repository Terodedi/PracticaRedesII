#!/usr/bin/env python3

import socket
import os.path
import sys
import struct
import signal
import time

def signal_handler(sig, frame):
    print('Has presionado Cntrl+C, Adios')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

class Servidor():
    def presentacion(self):
        print("Práctica RedesII 2018/2019\nDiseñada por Teresa Rodríguez de Dios\nEscuela Superior de Informática. UCLM.")

    def eleccion(self, instruccion):
        print('El servidor ha decodificado la instruccion [',instruccion,']. Va a proceder a interpretarla')

    def ya_existe(self, argumentos):
        print('El el nombre del archivo a transferir [',argumentos,'] ya existe, procedemos a cambiarlo...')

    def problemas_comandos(self):
        print('Estas escribiendo mal la llamada al cliente')
        print('Sintaxis correcta: servidorudp.py -p PUERTO')
        print('PUERTO hace referencia al puerto en el que esta atendiendo peticiones este servidor')

    def problemas_interprete(self, direccion):
        print('El servidor no es capaz de interpretar el comando del cliente [', direccion, ']')

    def inicio(self, switch):
        if switch:
            instruccion = 'WRITE'
        else:
            instruccion = 'READ'
        print("Se ejecutará la instrucción ",instruccion)

    def fin(self, switch):
        if switch:
            instruccion = 'WRITE'
        else:
            instruccion = 'READ'
        print("Finalizada instrucción ",instruccion)

IP = '127.0.0.1'
try:
    PUERTO = int(sys.argv[2])
except:
    Servidor().problemas_comandos()
    sys.exit(1)
CHUNK_SIZE = 10240


class Instrucciones():
    def __init__(self, size, timeout):
        self.timeout = timeout
        self.size = 512
        if size != 512:
            self.size = size

    def write(self,argumentos,socket,direccion):
        Servidor().inicio(True)
        if os.path.isfile(('archivosS/'+argumentos)):
            print('ERROR : El fichero ya esta creado')
            socket.sendto(struct.pack('!HH%dsB'% len("File already exists".encode()),5,6,"File already exists".encode(),0), direccion)
            return
        id_previo = 0
        socket.sendto(struct.pack('!HH',4,0), direccion)
        with open(('archivosS/'+argumentos), "wb") as archivo:
            while True:
                fragmento, direccion = socket.recvfrom(CHUNK_SIZE)
                time.sleep(self.timeout)
                id_fragmento = struct.unpack('!H', fragmento[2:4])[0]
                fragmentoAux = fragmento[4:]
                socket.sendto(struct.pack('!HH',4,id_fragmento), direccion)
                if id_fragmento - 1 == id_previo:
                    if len(fragmentoAux) > 16:
                        print('[', id_fragmento, '] - RECIBO: ', fragmentoAux[:15], '...')
                    archivo.write(fragmentoAux)
                    id_previo = id_previo + 1
                if len(fragmentoAux) < self.size:
                    if self.size != 512:
                        fragmento, direccion = socket.recvfrom(CHUNK_SIZE)
                    break
        Servidor().fin(True)

    def read(self,argumentos,socket,direccion):
        Servidor().inicio(False)
        if not os.path.isfile(('archivosS/'+argumentos)):
            print('ERROR : El fichero no existe')
            socket.sendto(struct.pack('!HH%dsB'% len("File not found".encode()),5,1,"File not found".encode(),0), direccion)
            return

        id_file = 0
        with open(('archivosS/' + argumentos), 'rb') as archivo:
            if self.size != 512:
                ack, direccion = socket.recvfrom(CHUNK_SIZE)
            fragmento = archivo.read(self.size)
            while fragmento:
                id_file = id_file + 1
                fmt = b'!HH'
                cabecera_fragmento = struct.pack(fmt, 3, id_file)
                fragmento = cabecera_fragmento + fragmento
                if len(fragmento) > 20:
                    print('[', id_file, '] - ENVIO: ', fragmento[4:15], '...')
                time.sleep(self.timeout)
                socket.sendto(fragmento, direccion)
                ack, direccion = socket.recvfrom(CHUNK_SIZE)
                id_fileack = struct.unpack('!H', ack[2:4])[0]
                id_ack = struct.unpack('!H', ack[0:2])[0]
                fragmento = archivo.read(self.size)
            print('\nfin.')
        Servidor().fin(False)

def int_to_bytes(x):
    return x.to_bytes((x.bit_length() + 7) // 8, 'big')

def int_from_bytes(xbytes):
    return int.from_bytes(xbytes, 'big')

class Main():
    def __init__(self):
        if len(sys.argv) != 3:
            Servidor().problemas_comandos()
            sys.exit(1)
        else:
            if sys.argv[1] != '-p':
                Servidor().problemas_comandos()
                sys.exit(1)
            else:
                if not isinstance(int(sys.argv[2]), int):
                    Servidor().problemas_comandos()
                    sys.exit(1)

    def principal(self, socket):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, socket.SO_RCVTIMEO)
            while True:
                s.bind((IP, PUERTO))
                while True:
                    argumentos, direccion = s.recvfrom(CHUNK_SIZE)
                    if not argumentos:
                        print('El cliente se ha desconectado')
                        break
                    self.procesar_instruccion(argumentos, direccion, s)

    def procesar_instruccion(self, argumentos, direccion, socket):
        blocksize = 512
        timeout = 0
        instruccion = struct.unpack('!H', argumentos[:2])
        instruccion = instruccion[0]
        nameEnd = argumentos.find(b'\0',2)
        nombre = argumentos[2:nameEnd].decode()
        argumentos = argumentos[nameEnd+7:] #7 del 0octet0
        if instruccion == 1 or instruccion == 2:
            if len(argumentos) > 0:
                print('Se recibe peticion con parametros adicionales: ',argumentos)
                byte = False
                opcion = True
                valor = False
                texto_previo = True
                posible = ''
                while argumentos:
                    if byte:
                        desechar = struct.unpack('!B', argumentos[:1])
                        argumentos = argumentos[1:]
                        byte = False
                        if texto_previo:
                            valor = True
                            texto_previo = False
                        else:
                            valor = False
                            texto_previo = True
                    elif opcion:
                        posible = struct.unpack('!7s', argumentos[:7])[0].decode()
                        argumentos = argumentos[7:]
                        byte = True
                        texto_previo = True
                        valor = True
                        opcion = False
                    elif valor:
                        n = argumentos.find(b'\0',1)
                        n_valor = struct.unpack('!'+str(n)+'s', argumentos[:n])[0]
                        if posible == 'timeout':
                            timeout = int(n_valor)
                        elif posible == 'blksize':
                            blocksize = int(n_valor)
                        n_valor = int(n_valor)
                        argumentos = argumentos[len(str(n_valor)):]
                        opcion = True
                        byte = True
                        valor = False

                oack = b''
                if timeout != 0:
                    oack += struct.pack('!7sB'+str(len(str(timeout)))+'sB', b'timeout', 0, str(timeout).encode(), 0)
                if blocksize != 512:
                    oack += struct.pack('!7sB'+str(len(str(blocksize)))+'sB', b'blksize', 0, str(blocksize).encode(), 0)
                oack = struct.pack('!H', 6) + oack

                print('Enviando al cliente OACK con las opciones interpretadas. Estructura del OACK: ', oack)
                if (instruccion == 1 and os.path.isfile(('archivosS/' + nombre))) or (instruccion == 2 and not os.path.isfile(('archivosS/' + nombre))):
                    socket.sendto(oack, direccion)
            else:
                print('Se recibe peticion sin parametros adicionales y por tanto no envia OACK')
            Servidor().eleccion(instruccion)
            if instruccion == 1:
                Instrucciones(blocksize, timeout).read(nombre, socket, direccion)
            elif instruccion == 2:
                Instrucciones(blocksize, timeout).write(nombre, socket, direccion)
            else:
                Servidor().problemas_interprete(direccion)

Servidor().presentacion()
Main().principal(socket)
