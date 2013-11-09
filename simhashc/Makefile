CC=g++
GCC=gcc
CFLAGS=-c -Wall -I./include -I./ -O3 

ST_SOURCES=src/stem.c
ST_OBJECTS=$(ST_SOURCES:.cpp=o)
ST_EXECUTABLE=stem

CH_SOURCES=src/charikar/shash.c src/charikar/simi.c src/charikar/simiw.c src/charikar/lookup3.c
CH_OBJECTS=$(CH_SOURCES:.cpp=.o)
CH_EXECUTABLE=charikar

all: stem charikar

stem: $(ST_SOURCES) $(ST_EXECUTABLE)

$(ST_EXECUTABLE): $(ST_OBJECTS)
	$(GCC) -O3 -o $@ $(ST_SOURCES)

stem.o: src/stem.c

clean:
	rm -fr src/stem/*.o stem *~ src/shingles/*~ src/charikar/*~ src/charikar/*.o charikar

charikar: $(CH_SOURCES) $(CH_EXECUTABLE)

$(CH_EXECUTABLE): $(CH_OBJECTS)
	$(CC) $(CH_OBJECTS) -o $@

shash.o: src/charikar/shash.c src/charikar/simi.h src/charikar/simiw.h
simi.o: src/charikar/simi.c src/charikar/simi.h src/charikar/lookup3.h
simiw.o: src/charikar/simiw.c src/charikar/simiw.h src/charikar/lookup3.h
lookup3.o: src/charikar/lookup3.c src/charikar/lookup3.h
