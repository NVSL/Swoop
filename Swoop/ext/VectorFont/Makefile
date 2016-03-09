

default:
	python makeLetters.py
	for i in ??.brd ???.brd; do\
	    runEagleCam.py --cam extractFont.cam --brd $i --dir . --zip foo.zip --eagle $EAGLE_EXE --strong_flags;\
	done

	python VectorFont.py ??.plc ???.plc > VectorFontData.py	


clean:
	rm -rf *.plc *.gpi *.brd
	rm -rf *~
	rm -rf *.zip
	rm -rf *\#*
