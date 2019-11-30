#!/usr/bin/env python3

import socket
import threading
import os.path
import sys
import struct
import time
import signal

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
        print('Sintaxis correcta: servidortcp.py -p PUERTO')
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

    def write(self,argumentos,socket):
        Servidor().inicio(True)
        if os.path.isfile(('archivosS/' + argumentos)):
            print('ERROR : El fichero ya esta creado')
            socket.send(struct.pack('!HH%dsB' % len("File already exists".encode()), 5, 6, "File already exists".encode(), 0))
            return
        id_previo = 0
        socket.send(struct.pack('!HH', 4, 0))
        with open(('archivosS/' + argumentos), "wb") as archivo:
            while True:
                fragmento = socket.recv(self.size+4)
                time.sleep(self.timeout)
                id_fragmento = struct.unpack('!H', fragmento[2:4])[0]
                fragmentoAux = fragmento[4:]
                if id_fragmento - 1 == id_previo:
                    if len(fragmentoAux) > 16:
                        print('[', id_fragmento, '] - RECIBO: ', fragmentoAux[:15], '...')
                    archivo.write(fragmentoAux)
                    id_previo = id_previo + 1
                if len(fragmentoAux) < self.size:
                    break
        Servidor().fin(True)


    def read(self,argumentos,socket):
        Servidor().inicio(False)
        if not os.path.isfile(('archivosS/' + argumentos)):
            print('ERROR : El fichero no existe')
            socket.send(struct.pack('!HH%dsB' % len("File not found".encode()), 5, 1, "File not found".encode(), 0))
            return

        id_file = 0
        with open(('archivosS/' + argumentos), 'rb') as archivo:
            fragmento = archivo.read(self.size)
            print('Datos fichero ', fragmento)
            while fragmento:
                id_file = id_file + 1
                fmt = b'!HH%ds' % len(fragmento)
                fragmento = struct.pack(fmt, 3, id_file, fragmento)
                if len(fragmento) > 20:
                    print('[', id_file, '] - ENVIO: ', fragmento[4:15], '...')
                time.sleep(self.timeout)
                socket.send(fragmento)
                fragmento = archivo.read(self.size)
            print('\nfin.')
        Servidor().fin(False)


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

    def principal(self, socketlib):
        with socketlib.socket(socketlib.AF_INET, socketlib.SOCK_STREAM) as socket:
            socket.setsockopt(socketlib.SOL_SOCKET, socketlib.SO_REUSEADDR, 1)
            socket.bind((IP, PUERTO))
            socket.listen()
            while True:
                thread_socket, direccion = socket.accept()
                thread_socket.settimeout(60)
                threading.Thread(target=self.atender_cliente_puerto, args=(thread_socket, direccion)).start()

    def atender_cliente_puerto(self, socket, direccion):
        while True:
            try:
                argumentos = socket.recv(CHUNK_SIZE)
                if argumentos:
                    self.procesar_instruccion(argumentos, direccion, socket)
            except:
                socket.close()

    def procesar_instruccion(self, argumentos, direccion, socket):
        blocksize = 512
        timeout = 0
        instruccion = struct.unpack('!H', argumentos[:2])
        instruccion = instruccion[0]
        nameEnd = argumentos.find(b'\0',2)
        nombre = argumentos[2:nameEnd].decode()
        argumentos = argumentos[nameEnd+7:] #7 del 0octet0
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
                socket.send(oack)
        else:
            print('Se recibe peticion sin parametros adicionales y por tanto no envia OACK')
        Servidor().eleccion(instruccion)
        if instruccion == 1:
            Instrucciones(blocksize, timeout).read(nombre, socket)
        elif instruccion == 2:
            Instrucciones(blocksize, timeout).write(nombre, socket)
        else:
            Servidor().problemas_interprete(direccion)

Servidor().presentacion()
Main().principal(socket)
