###
#
# PSAU - PESQUISA DE SATISFAÇÃO DOS USUÁRIOS
# 
# Script de automação da geração de analises estatística
#
# Author: Herson Melo <hersonpc@gmail.com>
#
###

###
# Ambiente
###

setwd(dirname(sys.frame(1)$ofile))
output.path <- file.path(getwd(), "output")
dir.create(output.path, showWarnings = FALSE)

#Sys.setlocale("LC_ALL", "pt_PT.1252") # Make sure not to omit the `"LC_ALL",` first argument, it will fail.
#Sys.setlocale("LC_ALL", "pt_PT.CP1252") # the name might need to be 'CP1252'

# next try IS08859-1(/'latin1'), this works for me:
#Sys.setlocale("LC_ALL", "pt_PT.ISO8859-1")

###
# Bibliotecas
###

diretorio.raiz.report <- file.path(output.path, 
                                   format(Sys.Date(), "%Y-%m-%d"))
dir.create(diretorio.raiz.report, recursive = T, showWarnings = FALSE)

source(file.path(getwd(), "rpsau-novo-relatorio.R"), encoding = 'UTF-8') #ISO_8859-2

# 
# rmarkdown::render(file.path(getwd(), 'rpsau-report.Rmd'),
#                   output_file =  "index.html", 
#                   output_dir = diretorio.raiz.report, 
#                   encoding = 'UTF-8')

