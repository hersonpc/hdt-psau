###
## Análise estatística da Pesquisa de Satifação dos Usuários
## Hospital de Doenças Tropicais Dr. Anuar Auad
## 05 de Julho de 2017
###

months <- c("Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez")
months_full <- c("Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                 "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro")



###============================================================================
## Bibliotecas necessárias
###============================================================================

suppressWarnings(suppressPackageStartupMessages(library(reshape2)))
suppressWarnings(suppressPackageStartupMessages(library(dplyr)))
suppressWarnings(suppressPackageStartupMessages(library(lubridate)))
suppressWarnings(suppressPackageStartupMessages(library(ggplot2)))
suppressWarnings(suppressPackageStartupMessages(library(knitr)))
suppressWarnings(suppressPackageStartupMessages(library(scales)))
#suppressWarnings(suppressPackageStartupMessages(library(xlsx)))



###============================================================================
## Funções para ajustes
###============================================================================

ajusta_criterios <- function (field) {
  field <- tolower(iconv(as.character(field), to = "ASCII//TRANSLIT"))

  #field[field == "ótimo"] <- "otimo"
  field[field == "nao se aplica"] <- NA
  #ajustado <- as.factor(field)
  #ajustado <- as.factor(field, levels = c("ruim", "regular", "bom", "ótimo"))
  
  #message(str(field))
  ajustado <- factor(field, levels = c("ruim", "regular", "bom", "otimo"))
  return(as.numeric(ajustado))
}



###============================================================================
## Funções para normatização dos dados das pesquisas
###============================================================================

normatizar_pesquisa_geral <- function(pesquisa) {
  message('* Normatizando pesquisa geral...')
  
  # renomeando campos
  colnames(pesquisa) <- c("data", "nome", "data_internacao", "data_alta", 
                          "contato", "autorizo", "setor",
                          "a_1", "a_2", "a_3", 
                          "b_1", "b_2", "b_3", "b_4", 
                          "c_1", "c_2", "c_3", 
                          "d_1", "d_2", "d_3", 
                          "e_1", "e_2", 
                          "f_1", "f_2", "f_3", 
                          "g_1", "g_2", "g_3", 
                          "h_1", "h_2", "h_3", "h_4", "h_5", "h_6", "h_7", 
                          "elogios", "sugestoes", "reclamacoes", 
                          "mes_consolidacao", "id", "ano_consolidacao", "pesquisa_ativa", "equipe_pesquisa", "nps",
                          "quando_queixa", "periodo_queixa")
  
  pesquisa$id <- as.numeric(pesquisa$id)
  pesquisa$nome <- iconv(as.character(pesquisa$nome), to = "ISO_8859-2")
  pesquisa$contato <- iconv(as.character(pesquisa$contato), to = "ISO_8859-2")
  pesquisa$autorizo <- tolower(iconv(as.character(pesquisa$autorizo), to = "ISO_8859-2"))
  
  pesquisa$mes_consolidacao <- factor(as.character(pesquisa$mes_consolidacao), levels = months_full)
  pesquisa$data <- dmy_hms(pesquisa$data)
  pesquisa$data_internacao <- dmy(pesquisa$data_internacao)
  pesquisa$data_alta <- dmy(pesquisa$data_alta)
  pesquisa$setor <- as.factor(iconv(as.character(pesquisa$setor), to = "ISO_8859-2"))
  
  pesquisa$a_1 <- ajusta_criterios(pesquisa$a_1)
  pesquisa$a_2 <- ajusta_criterios(pesquisa$a_2)
  pesquisa$a_3 <- ajusta_criterios(pesquisa$a_3)
  pesquisa$m_a <- pesquisa %>% select(a_1:a_3) %>% rowMeans(na.rm = T)
  
  pesquisa$b_1 <- ajusta_criterios(pesquisa$b_1)
  pesquisa$b_2 <- ajusta_criterios(pesquisa$b_2)
  pesquisa$b_3 <- ajusta_criterios(pesquisa$b_3)
  pesquisa$b_4 <- ajusta_criterios(pesquisa$b_4)
  pesquisa$m_b <- pesquisa %>% select(b_1:b_4) %>% rowMeans(na.rm = T)

  pesquisa$c_1 <- ajusta_criterios(pesquisa$c_1)
  pesquisa$c_2 <- ajusta_criterios(pesquisa$c_2)
  pesquisa$c_3 <- ajusta_criterios(pesquisa$c_3)
  pesquisa$m_c <- pesquisa %>% select(c_1:c_3) %>% rowMeans(na.rm = T)
  
  pesquisa$d_1 <- ajusta_criterios(pesquisa$d_1)
  pesquisa$d_2 <- ajusta_criterios(pesquisa$d_2)
  pesquisa$d_3 <- ajusta_criterios(pesquisa$d_3)
  pesquisa$m_d <- pesquisa %>% select(d_1:d_3) %>% rowMeans(na.rm = T)
  
  pesquisa$e_1 <- ajusta_criterios(pesquisa$e_1)
  pesquisa$e_2 <- ajusta_criterios(pesquisa$e_2)
  pesquisa$m_e <- pesquisa %>% select(e_1:e_2) %>% rowMeans(na.rm = T)
  
  pesquisa$f_1 <- ajusta_criterios(pesquisa$f_1)
  pesquisa$f_2 <- ajusta_criterios(pesquisa$f_2)
  pesquisa$f_3 <- ajusta_criterios(pesquisa$f_3)
  pesquisa$m_f <- pesquisa %>% select(f_1:f_3) %>% rowMeans(na.rm = T)
  
  pesquisa$g_1 <- ajusta_criterios(pesquisa$g_1)
  pesquisa$g_2 <- ajusta_criterios(pesquisa$g_2)
  pesquisa$g_3 <- ajusta_criterios(pesquisa$g_3)
  pesquisa$m_g <- pesquisa %>% select(g_1:g_3) %>% rowMeans(na.rm = T)
  
  pesquisa$h_1 <- ajusta_criterios(pesquisa$h_1)
  pesquisa$h_2 <- ajusta_criterios(pesquisa$h_2)
  pesquisa$h_3 <- ajusta_criterios(pesquisa$h_3)
  pesquisa$h_4 <- ajusta_criterios(pesquisa$h_4)
  pesquisa$h_5 <- ajusta_criterios(pesquisa$h_5)
  pesquisa$h_6 <- ajusta_criterios(pesquisa$h_6)
  pesquisa$h_7 <- ajusta_criterios(pesquisa$h_7)
  pesquisa$m_h <- pesquisa %>% select(h_1:h_7) %>% rowMeans(na.rm = T)

  pesquisa$m_x <- pesquisa %>% select(m_a:m_h) %>% rowMeans(na.rm = T)  
  
  pesquisa$elogios <- iconv(as.character(pesquisa$elogios), to = "ISO_8859-2")
  pesquisa$sugestoes <- iconv(as.character(pesquisa$sugestoes), to = "ISO_8859-2")
  pesquisa$reclamacoes <- iconv(as.character(pesquisa$reclamacoes), to = "ISO_8859-2")
  

  pesquisa <- pesquisa %>% 
    mutate(ano = year(data), 
           mes = month(data))
  
  
  pesquisa <- pesquisa %>% filter(ano >= 2017)
  
  
  return(pesquisa)
}

normatizar_pesquisa_ambulatorio <- function(pesquisa) {
  message('* Normatizando pesquisa ambulatorio...')
  
  # renomeando campos
  colnames(pesquisa) <- c("data", "nome", "contato", "recepcao", "medico", "elogios", 
                          "reclamacoes", "sugestoes", "id", "mes_consolidacao", "atendente", "ano_consolidacao", "nps")
  
  # ajustando propriedades
  pesquisa$id <- as.numeric(pesquisa$id)
  pesquisa$data <- dmy_hms(pesquisa$data)
  pesquisa$mes_consolidacao <- factor(as.character(pesquisa$mes_consolidacao), levels = months_full)
  pesquisa$nome <- iconv(as.character(pesquisa$nome), to = "ISO_8859-2")
  pesquisa$contato <- iconv(as.character(pesquisa$contato), to = "ISO_8859-2")
                            
  pesquisa$recepcao <- ajusta_criterios(pesquisa$recepcao)
  pesquisa$medico <- ajusta_criterios(pesquisa$medico)
  
  pesquisa$m <- pesquisa %>% select(recepcao:medico) %>% rowMeans(na.rm=T)
  
  pesquisa$elogios <- iconv(as.character(pesquisa$elogios), to = "ISO_8859-2")
  pesquisa$sugestoes <- iconv(as.character(pesquisa$sugestoes), to = "ISO_8859-2")
  pesquisa$reclamacoes <- iconv(as.character(pesquisa$reclamacoes), to = "ISO_8859-2")
  
  pesquisa <- pesquisa %>% 
    mutate(ano = year(data), 
           mes = month(data))

    # retornando conclusão
  return(pesquisa)
}




###============================================================================
## Função de importação dos dados
###============================================================================

importar_dados_psau <- function() {
  message('Importando dados das pesquisas do PSAU...')
  
  # definindo url de origem...
  url.geral <- "https://docs.google.com/spreadsheets/d/1R38ZhGubZsMR3LC5pPCmdvy857XnGIrga6RroxBZ3U0/pub?gid=1725198295&single=true&output=csv"
  url.ambulatorio <- "https://docs.google.com/spreadsheets/d/1Vq1QQUPtXRcqvOsB8pPHVKq9aLDTp5_4OBLT7N0yBl4/pub?gid=476331211&single=true&output=csv"

  # baixando dados....
  message('Downloading data from Google Spreadsheets... #1')
  
  #baixando arquivos...
  dir.create(file.path(getwd(), "temp"), showWarnings = FALSE)
  download.file(url.geral, "temp/formulario.geral.csv", mode = "wb")
  download.file(url.ambulatorio, "temp/formulario.ambulatorio.csv", mode = "wb")
  
  # carregando arquivos...
  pesq.geral <- read.csv("temp/formulario.geral.csv", fileEncoding = 'UTF-8')
  pesq.ambulatorio <- read.csv("temp/formulario.ambulatorio.csv", fileEncoding = 'UTF-8')
  
  # removendo temporarios...
  file.remove(list.files(file.path(getwd(), "temp"), full.names = T))
  
  
  #pesq.geral <- read.csv(url.geral, fileEncoding = 'UTF-8') #, na.strings = c(""," ","NA")
  message('Downloading data from Google Spreadsheets... #2')
  #pesq.ambulatorio <- read.csv(url.ambulatorio, fileEncoding = 'UTF-8') #, na.strings = c(""," ","NA")

  # normatizando dados...
  pesq.geral <- normatizar_pesquisa_geral(pesq.geral)
  pesq.ambulatorio <- normatizar_pesquisa_ambulatorio(pesq.ambulatorio)

  # informações de log...
  message('--[ Resumo PSAU ]-------------------------------------------')
  message(paste0('  - Pesquisa geral tem ', nrow(pesq.geral), ' respostas (', format(object.size(pesq.geral), units = "auto"), ')'))
  message(paste0('  - Pesquisa ambulatorio tem ', nrow(pesq.ambulatorio), ' respostas (', format(object.size(pesq.ambulatorio), units = "auto"), ')'))

  # exportando dados...
  
    
  # montando estrutura de saida...
  return( list("p1" = tbl_df(pesq.geral), 
               "p1_medias" = tbl_df(pesq.geral %>% select(ano = ano_consolidacao, mes = mes_consolidacao, m_a:m_x)),
               "p2" = tbl_df(pesq.ambulatorio),
               "p2_medias" = tbl_df(pesq.ambulatorio %>% select(ano = ano_consolidacao, mes = mes_consolidacao, recepcao:medico, m))
               ) 
          )
}



###============================================================================
## Execução do tratamento das informações
###============================================================================

pesquisas <- importar_dados_psau();

#str(pesquisas$p1)

