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

###
# Bibliotecas
###

diretorio.raiz.report <- file.path(output.path, 
                                   format(Sys.Date(), "%Y-%m-%d"))
dir.create(diretorio.raiz.report, recursive = T, showWarnings = FALSE)


rmarkdown::render(file.path(getwd(), 'rpsau-report.Rmd'),
                  output_file =  "index.html", 
                  output_dir = diretorio.raiz.report)

