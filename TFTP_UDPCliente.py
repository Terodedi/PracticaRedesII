#!/usr/bin/env python3

import socket
import os.path
import sys
import signal
import struct
import time

def signal_handler(sig, frame):
    print('Has presionado Cntrl+C, Adios')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def unpack_helper(fmt, data):
    size = struct.calcsize(fmt)
    return struct.unpack(fmt, data[:size]), data[size:]

class Usuario():
    def presentacion(self):
        print("Práctica RedesII 2018/2019\nDiseñada por Teresa Rodríguez de Dios\nEscuela Superior de Informática. UCLM.")

    def eleccion(self,instruccion):
        print("Ha seleccionado la instrucción", instruccion)

    def verificarInstruccion(self):
        instruccion = input('TFTP@UDP> ')
        argumentos = instruccion.split(" ")
        if (argumentos[0] != 'WRITE' and argumentos[0] != 'READ' and argumentos[0] != 'QUIT'):
            while (argumentos[0] != 'WRITE' and argumentos[0] != 'READ' and argumentos[0] != 'QUIT'):
                print("Error. La instrucción solicitada no existe.\nVuelva a intentarlo.")
                instruccion = input('TFTP@UDP> ')
                argumentos = instruccion.split(" ")

        return argumentos

    def problemas_comandos(self):
        print('Estas escribiendo mal la llamada al cliente')
        print('Sintaxis correcta: clienteudp.py -s IP -p PUERTO')
        print('PUERTO hace referencia al puerto en el que esta atendiendo peticiones el servidor')
        print('IP hace referencia a la direccion IP en la que esta atendiendo peticiones el servidor')

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


try:
    socket.inet_aton(sys.argv[2])
    IP = sys.argv[2]
except:
    Usuario().problemas_comandos()
    sys.exit(1)
try:
    PUERTO = int(sys.argv[4])
except:
    Usuario().problemas_comandos()
    sys.exit(1)
CHUNK_SIZE = 10240

class Instrucciones():
    def __init__ (self, blocksize, timeout):
        self.size = 512
        self.timeout = timeout
        if blocksize != 0:
            self.size = blocksize

    def Inicio(self, codigo_operacion, nombre_archivo, modo_operacion):
        if self.size != 512 and self.timeout != 0:
            datos = struct.pack('!H' + str(len(nombre_archivo.encode())) + 'sB' + str(len(modo_operacion.encode())) + 'sB' + str(len("timeout".encode())) + 'sB' + str(len(str(self.timeout))) + 'sB' + str(len("blksize".encode())) + 'sB' + str(len(str(self.size))) + 'sB', codigo_operacion, nombre_archivo.encode(), 0, modo_operacion.encode(), 0, "timeout".encode(), 0, str(self.timeout).encode(), 0, "blksize".encode(),0,str(self.size).encode(), 0)
        elif self.timeout != 0:
            datos = struct.pack('!H' + str(len(nombre_archivo.encode())) + 'sB' + str(len(modo_operacion.encode())) + 'sB' + str(len("timeout".encode())) + 'sB' + str(len(str(self.timeout))) + 'sB', codigo_operacion, nombre_archivo.encode(), 0, modo_operacion.encode(), 0, "timeout".encode(), 0, str(self.timeout).encode(), 0)
        elif self.size != 512:
            datos = struct.pack('!H' + str(len(nombre_archivo.encode())) + 'sB' + str(len(modo_operacion.encode())) + 'sB'+str(len("blksize".encode())) + 'sB' + str(len(str(self.size))) + 'sB', codigo_operacion, nombre_archivo.encode(), 0, modo_operacion.encode(), 0, "blksize".encode(),0,str(self.size).encode(), 0)
        else:
            datos = struct.pack('!H' + str(len(nombre_archivo.encode())) + 'sB' + str(len(modo_operacion.encode())) + 'sB', codigo_operacion, nombre_archivo.encode(), 0, modo_operacion.encode(), 0)
        return datos

    def oack(self, socket):
        oackpack, direccion = socket.recvfrom(CHUNK_SIZE)
        print('Recibo OACK del servidor: ', oackpack)
        n_ack, restante = unpack_helper(('!H'), oackpack)
        if n_ack[0] == 6:
            ch, restante = unpack_helper(('!7s'), restante)
            if ch[0] == b'blksize':
                n = restante.find(b'\x00', 1)
                size_server = struct.unpack('!'+str((n - 1)) + 's', restante[1:n])
                restante = restante[n:]
                if int(size_server[0]) == self.size:
                    print('Se ha interpretado correctamente la peticion de longitud con valor: [', self.size, ']')
                else:
                    self.size = 512
            elif ch[0] == b'timeout':
                n = restante.find(b'\x00', 1)
                timeout_server = struct.unpack('!'+str((n - 1)) + 's', restante[1:n])
                restante = restante[n:]
                if int(timeout_server[0]) == self.timeout:
                    print('Se ha interpretado correctamente la peticion de tiempo con valor: [', self.timeout, ']')
                else:
                    self.timeout = 0
            else:
                self.timeout = 0
                self.size = 512

            if len(restante) > 9:
                cero, restante = unpack_helper(('!B'), restante)
                ch, restante = unpack_helper(('!7s'), restante)
                if ch[0] == b'blksize':
                    n = restante.find(b'\x00', 1)
                    size_server = struct.unpack('!' + str((n - 1)) + 's', restante[1:n])
                    if int(size_server[0]) == self.size:
                        print('Se ha interpretado correctamente la peticion de longitud con valor: [', self.size, ']')
                    else:
                        self.size = 512
                elif ch[0] == b'timeout':
                    n = restante.find(b'\x00', 1)
                    timeout_server = struct.unpack('!' + str((n - 1)) + 's', restante[1:n])
                    if int(timeout_server[0]) == self.timeout:
                        print('Se ha interpretado correctamente la peticion de tiempo con valor: [', self.timeout, ']')
                    else:
                        self.timeout = 0
                else:
                    self.timeout = 0
                    self.size = 512
        else:
            self.timeout = 0
            self.size = 512

    def write(self,argumentos,socket):
        Usuario().inicio(True)
        if os.path.isfile(('archivosC/'+argumentos)):
            socket.sendto(self.Inicio(2, argumentos, 'octet'), (IP, PUERTO))
            if self.size != 512 or self.timeout != 0: # Esperamos OACK para ver que ha entendido el servidor
                self.oack(socket)

            respuesta, direccion = socket.recvfrom(CHUNK_SIZE)
            codigo_operacion = struct.unpack('!H', respuesta[0:2])[0]
            numero_fragmento = struct.unpack('!H', respuesta[2:4])[0]
            if codigo_operacion == 4:
                with open(('archivosC/' + argumentos), 'rb') as archivo:
                    fragmento = archivo.read(self.size)

                    while fragmento:
                        numero_fragmento = numero_fragmento + 1
                        fmt = b'!HH%ds' % len(fragmento)
                        fragmento = struct.pack(fmt, 3, numero_fragmento, fragmento)
                        if len(fragmento) > 20:
                            print('[',numero_fragmento,'] - ENVIO: ',fragmento[4:15], '...')
                        time.sleep(self.timeout)
                        socket.sendto(fragmento, direccion)

                        ack, direccion = socket.recvfrom(CHUNK_SIZE)
                        id_fileack = struct.unpack('!H', ack[2:4])[0]
                        if numero_fragmento != id_fileack:
                            return
                        fragmento = archivo.read(self.size)
                    if self.size != 512:
                        socket.sendto(b'', direccion)
            else:
                if codigo_operacion == 5:
                    codigo_error = struct.unpack('!H', respuesta[2:4])[0]
                    if codigo_error == 1:
                        print('Codigo error [', codigo_error, ']: ',respuesta[4:(respuesta.find(b'\0',4))].decode())
                    elif codigo_error ==6:
                        print('Codigo error [', codigo_error, ']: ',respuesta[4:(respuesta.find(b'\0',4))].decode())
                    else:
                        print('Codigo error [', codigo_error, '] no registrado en el sistema')
                else:
                    print('Codigo de operacion no registrado')
        else:
            print('ERROR, el archivo no existe.')
        Usuario().fin(True)

    def read(self,argumentos,socket):
        Usuario().inicio(False)
        nom_arch = argumentos
        if not(os.path.isfile(('archivosC/' + nom_arch))):
            socket.sendto(self.Inicio(1, argumentos, 'octet'), (IP, PUERTO))
            if self.size != 512 or self.timeout != 0: # Esperamos OACK para ver que ha entendido el servidor
                self.oack(socket)

            with open(('archivosC/' + nom_arch), "wb") as archivo:
                if self.size != 512:
                    socket.sendto(struct.pack('!HH', 4, 0), (IP, PUERTO))
                while True:
                    fragmento, direccion = socket.recvfrom(CHUNK_SIZE)
                    codigo_operacion, fragmento = unpack_helper('!H', fragmento)
                    codigo_operacion = codigo_operacion[0]
                    if codigo_operacion == 5:
                        codigo_error = struct.unpack('!H', fragmento[2:4])[0]
                        if codigo_error == 1:
                            print('Codigo error [', codigo_error, ']: ',
                                  fragmento[4:(fragmento.find(b'\0', 4))].decode())
                        elif codigo_error == 6:
                            print('Codigo error [', codigo_error, ']: ',
                                  fragmento[4:(fragmento.find(b'\0', 4))].decode())
                        else:
                            print('Codigo error [', codigo_error, '] no registrado en el sistema')
                        break
                    elif codigo_operacion == 3:
                        id_fragmento, fragmento = unpack_helper('!H', fragmento)
                        id_fragmento = id_fragmento[0]
                        if len(fragmento) > 16:
                            print('[',id_fragmento,'] - RECIBO: ',fragmento[:15], '...')
                        archivo.write(fragmento)
                        socket.sendto(struct.pack('!HH', 4, id_fragmento), direccion)
                        if len(fragmento) < self.size:
                            break
                print('\nfin.')
        else:
            print('ERROR, el archivo que pretende leer ya existe')
        Usuario().fin(False)

    def quit(self):
        print('Fin del programa.')
        posible = True
        return posible


class Main():
    def __init__(self):
        if len(sys.argv) != 5:
            Usuario().problemas_comandos()
            sys.exit(1)
        else:
            if sys.argv[1] != '-s':
                Usuario().problemas_comandos()
                sys.exit(1)
            else:
                if not isinstance(sys.argv[2], str):
                    Usuario().problemas_comandos()
                    sys.exit(1)
                else:
                    # Compruebo que la direccion indicada por el usuario sea una IP valida
                    try:
                        socket.inet_aton(sys.argv[2])
                    except:
                        Usuario().problemas_comandos()
                        sys.exit(1)
                    if sys.argv[3] != '-p':
                        Usuario().problemas_comandos()
                        sys.exit(1)
                    else:
                        if not isinstance(int(sys.argv[4]), int):
                            Usuario().problemas_comandos()
                            sys.exit(1)

    def principal(self,socket):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as socket:
            socket.connect((IP, PUERTO))
            posible = False
            while not (posible):
                instruccion = Usuario().verificarInstruccion()
                size = 512
                timeout = 0
                if instruccion[0] != 'QUIT':
                    if len(instruccion) > 3:
                        if instruccion[2] == '-size':
                            size = int(instruccion[3])
                        elif instruccion[2] == '-timeout':
                            timeout = int(instruccion[3])
                        if len(instruccion) > 5:
                            if instruccion[4] == '-size':
                                size = int(instruccion[5])
                            elif instruccion[4] == '-timeout':
                                timeout = int(instruccion[5])
                Usuario().eleccion(instruccion)
                if instruccion[0] == 'WRITE':
                    Instrucciones(size, timeout).write(instruccion[1], socket)

                elif instruccion[0] == 'READ':
                    Instrucciones(size, timeout).read(instruccion[1], socket)

                elif instruccion[0] == 'QUIT':
                    posible = Instrucciones(size, timeout).quit()

Usuario().presentacion()
Main().principal(socket)
