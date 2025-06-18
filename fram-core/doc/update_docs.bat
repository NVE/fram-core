@echo on
call make clean
call sphinx-apidoc -o ./source/modules/ ../src/core/
call make html