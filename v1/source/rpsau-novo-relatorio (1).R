###
## Importação das bibliotecas
###
if(!require(reshape2, quietly = T, warn.conflicts = F)){install.packages("reshape2")}
if(!require(dplyr, quietly = T, warn.conflicts = F)){install.packages("dplyr")}
if(!require(tidyr, quietly = T, warn.conflicts = F)){install.packages("tidyr")}
if(!require(lubridate, quietly = T, warn.conflicts = F)){install.packages("lubridate")}
if(!require(ggplot2, quietly = T, warn.conflicts = F)){install.packages("ggplot2")}
if(!require(knitr, quietly = T, warn.conflicts = F)){install.packages("knitr")}
if(!require(scales, quietly = T, warn.conflicts = F)){install.packages("scales")}
if(!require(grid, quietly = T, warn.conflicts = F)){install.packages("grid")}
if(!require(gridExtra, quietly = T, warn.conflicts = F)){install.packages("gridExtra")}
if(!require(htmlTable, quietly = T, warn.conflicts = F)){install.packages("htmlTable")}
if(!require(zip, quietly = T, warn.conflicts = F)){install.packages("zip")}
if(!require(mailR, quietly = T, warn.conflicts = F)){install.packages("mailR")}



###
## Importação dos dados já estruturados
###
source(file.path(getwd(), "rpsau-data.R"), encoding = 'UTF-8')


###
## Funções e variaveis de apoio
###
trim <- function (x) gsub("^\\s+|\\s+$", "", x)
html_mail_table = data.frame();
outputDir = getwd();

###
## Funções de extratificação de dados
###
consolidacoes <- function(selAno, selMes) {
  
  outputDir <<- file.path(getwd(), 'output', selAno, selMes)
  message(paste0('      -- Consolidacao ', selAno, '/', selMes, ' -> ', outputDir))
  
  # Criando agrupamentos de dados
  tmp_periodo_geral <- pesquisas$p1_medias %>% filter(ano == selAno & mes == selMes) %>% select(m_a:m_h)
  tmp_periodo_amb <- pesquisas$p2_medias %>% filter(ano == selAno & mes == selMes) %>% select(m)
  
  # Totalizando os agrupamentos por colunas
  tmp_consolidado_geral <- tmp_periodo_geral %>% colMeans(na.rm=T) * 100 / 4
  tmp_consolidado_amb <- tmp_periodo_amb %>% colMeans(na.rm=T) * 100 / 4
  
  # Unificando dados do ambulatorio
  tmp_consolidado_geral[["m_y"]] <- tmp_consolidado_amb
  
  # Consolidando media de avaliacao geral
  tmp_consolidado_geral[["m_geral"]] <- tmp_consolidado_geral %>% sapply(as.numeric) %>% mean(na.rm = TRUE)
  
  nome_medidas <- c("Recepção", "Médico", "Enfermagem", "Serviço Social", "Pscicologia", 
                    "Nutrição", "Reabilitação", "Infraestrutura", "Ambulatório", "Geral")
  names(tmp_consolidado_geral) <- nome_medidas
  
  resumo_mes <- melt(tmp_consolidado_geral, variable.name = "medida", value.name = "percentual")
  resumo_mes <- cbind(medida = rownames(resumo_mes), resumo_mes)
  rownames(resumo_mes) <- NULL
  resumo_mes$medida <- factor(resumo_mes$medida, levels = unique(nome_medidas))
  
  #print(resumo_mes)
  
  p1 <- ggplot(resumo_mes, aes(x=medida, y=percentual)) +
    geom_bar(stat = "identity", fill = c(rep("#4b76bc", each=9), "#d63924")) +
    geom_text(aes(label = paste0(round(percentual, 2), '%')), vjust = -0.7) +
    coord_cartesian(ylim = c(0, 100)) +
    geom_hline(aes(yintercept=80), colour="#990000", linetype="dashed") + 
    theme_bw() +
    theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
    labs(title = paste0("Avaliação do grau de satisfação dos usuários - ", selMes, "/", selAno), 
         subtitle = "Hospital de Doenças Tropicais Dr. Anuar Auad", 
         #caption = paste("Pesquisa realizada com", nrow(resumo2), "pessoas."),
         x = "",
         y = "Frequencia relativa")
  
  # Preparando pasta para imagens
  dir.create(outputDir, recursive = T, showWarnings = FALSE)
  
  png(file.path(outputDir, "plot01.png"), 
      height=4, width=8, units = 'in', res = 300)
  print(p1)
  dev.off()
  ##----------------------------------------------------------------------------------------------------
  
  
  
  ###
  ## Consolidando Quantidade de Ruim, Regular, Bom e Otimos
  ###
  
  # Pesquisa Geral
  a <- pesquisas$p1 %>% filter(year(data) == selAno & mes_consolidacao == selMes) %>% select(a_1:h_7)
  b <- a %>% lapply(table) %>% lapply(as.data.frame) %>% Map(cbind, var = names(a),.) %>% bind_rows() %>% dcast(var ~ Var1)
  #message(names(b))
  names(b)[names(b) == "var"] <- "x"
  names(b)[names(b) == "1"] <- "Ruim"
  names(b)[names(b) == "2"] <- "Regular"
  names(b)[names(b) == "3"] <- "Bom"
  names(b)[names(b) == "4"] <- "Otimo"
  #names(b) <- c("x", "Ruim", "Regular", "Bom", "Otimo")
  c <- b %>% select(2:length(names(b))) %>% colSums(na.rm=T) %>% melt
  c <- as.data.frame(cbind(avaliacao = rownames(c), freq = c$value))
  
  # Presquisa Ambulatorial
  a2 <- pesquisas$p2 %>% filter(year(data) == selAno & mes_consolidacao == selMes) %>% select(recepcao:medico)
  b2 <- a2 %>% lapply(table) %>% lapply(as.data.frame) %>% Map(cbind, var = names(a2),.) %>% bind_rows() %>% dcast(var ~ Var1)
  names(b2)[names(b2) == "var"] <- "x"
  names(b2)[names(b2) == "1"] <- "Ruim"
  names(b2)[names(b2) == "2"] <- "Regular"
  names(b2)[names(b2) == "3"] <- "Bom"
  names(b2)[names(b2) == "4"] <- "Otimo"
  #names(b2) <- c("x", "Ruim", "Regular", "Bom", "Otimo")
  c2 <- b2 %>% select(2:length(names(b2))) %>% colSums(na.rm=T) %>% melt
  c2 <- as.data.frame(cbind(avaliacao = rownames(c2), freq = c2$value))
  
  # Junção das pesquisas
  d <- merge(c, c2, by = "avaliacao") %>% 
    mutate(freq.x = as.numeric(as.character(freq.x)),
           freq.y = as.numeric(as.character(freq.y)),
           fr.x = (freq.x / sum(freq.x)) * 100,
           fr.y = (freq.y / sum(freq.y)) * 100,
           freq = freq.x + freq.y,
           fr = (freq / sum(freq)) * 100)
  
  d <- c %>% mutate(freq = as.numeric(as.character(c$freq)), fr = (freq / sum(freq)) *100 )
  
  # pie(d$fr, 
  #     labels = paste0(round(d$fr,2), '% ', d$avaliacao), 
  #     col = c("#71b777", "#2d9636", "#E69F00", "#b54a42"),
  #     main = paste0("Distribuição geral das avaliações - ", selMes, "/", selAno))
  png(file.path(outputDir, "plot02.png"), 
      height=4, width=6, units = 'in', res = 300)
  pie(d$fr, 
      labels = paste0(round(d$fr,2), '% ', d$avaliacao), 
      col = c("#71b777", "#2d9636", "#E69F00", "#b54a42"),
      main = paste0("Distribuição geral das avaliações - ", selMes, "/", selAno))
  dev.off()
  ##----------------------------------------------------------------------------------------------------
  
  
  
  ###
  ## Estatisticas por setor    
  ###
  
  s <- pesquisas$p1 %>% 
    filter(year(data) == selAno & mes_consolidacao == selMes) %>% 
    select(setor, m_x) %>% 
    group_by(setor) %>% 
    summarise(qtde = n())
  s$setor <- as.character(s$setor)
  s$setor <- sub('^$', "Não informado", s$setor)
  if(!is.na(s[s$setor == 'Ambulatório', 2])) {
    s[s$setor == 'Ambulatório', 2] <- s[s$setor == 'Ambulatório', 2] + nrow(pesquisas$p2 %>% 
                                                                              filter(year(data) == selAno & mes_consolidacao == selMes))
  } else {
    s <-  rbind(s, data.frame(
      'setor' = c('Ambulatório'),
      'qtde' = nrow(pesquisas$p2 %>% filter(year(data) == selAno & mes_consolidacao == selMes))
    )
    )
  }
  s[is.na(s$setor),1] <- "Não informado"
  s <- s[order(s$qtde, decreasing = T),]
  s$setor <- factor(s$setor, levels = s$setor)
  
  p2 <- ggplot(s, aes(x=setor, y=qtde)) + 
    geom_bar(stat = "identity", fill='#4c74b5') + 
    geom_text(aes(label = qtde), vjust = -0.7) +
    coord_cartesian(ylim = c(0, max(s$qtde) * 1.1)) +
    theme_bw() +
    theme(axis.text.x = element_text(angle = 45, hjust = 1)) +
    labs(title = paste0("Distribuição de origem dos formulários - ", selMes, "/", selAno), 
         subtitle = "Hospital de Doenças Tropicais Dr. Anuar Auad", 
         #caption = paste("Pesquisa realizada com", nrow(resumo2), "pessoas."),
         x = "",
         y = "N. de formulários respondidos")
  
  #print(p2)  
  png(file.path(outputDir, "plot03.png"), 
      height=4, width=8, units = 'in', res = 300)
  print(p2)  
  dev.off()
  ##----------------------------------------------------------------------------------------------------

  
  ###
  ## Extratificando elogios, reclamações e sugestões...
  ###
  
  message('Extraindo elogios, reclamações e sugestões...')
  dados.do.periodo.p1 <- pesquisas$p1 %>% filter(ano_consolidacao == selAno & mes_consolidacao == selMes)
  dados.do.periodo.p2 <- pesquisas$p2 %>% filter(ano_consolidacao == selAno & mes_consolidacao == selMes)
  
  grupo_elogios <- c(unique(dados.do.periodo.p1$elogios), unique(dados.do.periodo.p2$elogios)) %>%
    trim %>% unique %>% ifelse(. == "", NA, .) %>% as.data.frame %>% filter(!is.na(.))
  grupo_sugestoes <- c(unique(dados.do.periodo.p1$sugestoes), unique(dados.do.periodo.p2$sugestoes)) %>%
    trim %>% unique %>% ifelse(. == "", NA, .) %>% as.data.frame %>% filter(!is.na(.))
  grupo_reclamacoes <- c(unique(dados.do.periodo.p1$reclamacoes), unique(dados.do.periodo.p2$reclamacoes)) %>%
    trim %>% unique %>% ifelse(. == "", NA, .) %>% as.data.frame %>% filter(!is.na(.))
  
  if(nrow(grupo_elogios) > 0) {
    write.csv2(x = grupo_elogios, file = file.path(outputDir, paste0("elogios.", selAno, "-", selMes, ".csv")), fileEncoding = 'ISO_8859-2')
  }
  if(nrow(grupo_elogios) > 0) {
    write.csv2(x = grupo_sugestoes, file = file.path(outputDir, paste0("sugestoes.", selAno, "-", selMes, ".csv")), fileEncoding = 'ISO_8859-2')
  }
  if(nrow(grupo_reclamacoes) > 0) {
    write.csv2(x = grupo_reclamacoes, file = file.path(outputDir, paste0("reclamacoes.", selAno, "-", selMes, ".csv")), fileEncoding = 'ISO_8859-2')
  }
  
  
  ##
  # Análise dos atendentes no ambulatório
  ##
  message(paste('Análise dos atendentes no ambulatório', selAno, selMes))
  atendentes_amb <- pesquisas$p2 %>% 
    filter(ano_consolidacao == selAno & mes_consolidacao == selMes) %>% 
    group_by(atendente, recepcao) %>% 
    summarise(qtde = n())
  atendentes_amb <- atendentes_amb[complete.cases(atendentes_amb), ]
  
  atendentes_amb$recepcao <- replace(atendentes_amb$recepcao, atendentes_amb$recepcao == 1, "Ruim")
  atendentes_amb$recepcao <- replace(atendentes_amb$recepcao, atendentes_amb$recepcao == 2, "Regular")
  atendentes_amb$recepcao <- replace(atendentes_amb$recepcao, atendentes_amb$recepcao == 3, "Bom")
  atendentes_amb$recepcao <- replace(atendentes_amb$recepcao, atendentes_amb$recepcao == 4, "Otimo")
  
  relatorio_atendentes <- atendentes_amb %>% dcast(atendente ~ recepcao)
  relatorio_atendentes[is.na(relatorio_atendentes)] <- 0

  write.csv2(x = relatorio_atendentes, file = file.path(outputDir, paste0("ambulatorio.atendentes.", selAno, "-", selMes, ".csv")), fileEncoding = 'ISO_8859-2')
  
  
  ##----------------------------------------------------------------------------------------------------
  
  
  ###
  ##
  ###
  
  # calculando os total de cada grupo de pergunta
  q1a <- table(dados.do.periodo.p1 %>%
                 select(a_1:h_7) %>%
                 rowMeans(na.rm=T) %>%
                 ceiling) %>%
    melt
  q1b <- table(dados.do.periodo.p2 %>%
                 select(recepcao, medico) %>%
                 rowMeans(na.rm=T) %>%
                 ceiling) %>%
    melt
  
  # unindo as avaliações
  q1 <- merge(q1a, q1b, by="Var1") %>%
    mutate(total = value.x + value.y) %>%
    filter(Var1 >= 3) %>% # selecionando ótimos(4) e bons(3)
    colSums()
  
  t <- data.frame(
    Indicadores = c('QUANTIDADE DE AVALIAÇÕES ENTRE BOM E ÓTIMO NA PESQUISA DE SATISFAÇÃO',
                    'TOTAL DE PESSOAS PESQUISADAS NA PESQUISA DE SATISFAÇÃO'
    ),
    Resultados = c(as.numeric(q1['total']), 
                   nrow(dados.do.periodo.p1) + nrow(dados.do.periodo.p2)#,
                   # 0
    )
  )
  names(t) <- c(paste0('Indicadores - ', selMes, '/', selAno), "Resultados")
  
  
  html_mail_table <- htmlTable(t, rnames = FALSE)
  
  # write.csv2(x = t, file = file.path(outputDir, paste0("estatisticas.", selAno, "-", selMes, ".csv")), fileEncoding = 'ISO_8859-2')

  ##----------------------------------------------------------------------------------------------------
  
  
  ###
  ## Enviando e-mail
  ###
  
  sender <- "feedback.isgsaude@gmail.com" # Replace with a valid address
  recipients <- c("hersonpc@gmail.com", "assessoria.qualidade.hdt@isgsaude.org", "qualidade.hdt@isgsaude.org") # Replace with one or more valid addresses
  attach_files = c()
  # attach_files = c(file.path(outputDir, "plot01.png"), file.path(outputDir, "plot02.png"), file.path(outputDir, "plot03.png"))
  zipFile = file.path(outputDir, paste0('psau-', selAno, '-', selMes, '.zip'))
  message(zipFile)
  if(file.exists(zipFile)) {
    file.remove(zipFile)
    Sys.sleep(10)
  }
  if(!file.exists(zipFile)) {
    localDir = getwd()
    setwd(outputDir)
    zip(zipfile = zipFile, files = list.files(path = outputDir, full.names = FALSE))
    setwd(localDir)
    Sys.sleep(10)
  }
  if(file.exists(zipFile)) {
    attach_files = c(zipFile)
  }
  message('Enviando e-mail...')
  email <- send.mail(from = sender,
                     to = recipients,
                     subject = paste("Consolidação PSAU |", selMes, selAno, "-", format(Sys.time(), "%d/%m/%Y - %X")),
                     body = paste("Relatório de consolidação do PSAU<br><br>", html_mail_table),
                     html = TRUE,
                     attach.files = attach_files,
                     smtp = list(host.name = "smtp.gmail.com", port = 465, 
                                 user.name = "feedback.isgsaude@gmail.com",            
                                 passwd = "isg2015ISG", ssl = TRUE),
                     authenticate = TRUE,
                     send = TRUE)
  #email
  
  
}


###
## Extratificação de dados
###
# consolidacoes(2017, "Novembro")
# consolidacoes(2017, "Dezembro")
# consolidacoes(2018, "Janeiro")
# consolidacoes(2018, "Fevereiro")


args <- commandArgs(TRUE)
if (length(args) < 2) {
  writeLines('Informe os parametros para calculo da análise:')
  anoUser <- readline(paste0('Qual ano a ser processado? (', format(Sys.Date(), "%Y"), '): '))
  mesUser <- readline(paste0('Qual mês a ser processado? (', format(Sys.Date(), "%m"), '): '))
} else {
  anoUser <- args[1]
  mesUser <- args[2] 
}

if(anoUser == "") {
  anoUser <- as.integer(format(Sys.Date(), "%Y"))
} else {
  anoUser <- as.integer(anoUser)
}
if(mesUser == "") {
  mesUser <- as.integer(format(Sys.Date(), "%m"))
} else {
  mesUser <- as.integer(mesUser)
}

message(paste("parametros: ", (anoUser >= 2017) && (anoUser <= 2025) && !is.na(months_full[mesUser])))
message(paste("ano", anoUser))
message(paste("mesUser", mesUser, ' -> ', months_full[mesUser]))


if( (anoUser >= 2017) && (anoUser <= 2025) && !is.na(months_full[mesUser]) ) {
  consolidacoes(anoUser, months_full[mesUser])
} else {
  stop('Parametros inválidos para processamento!')
}


# a_consolidar <- pesquisas$p1 %>% group_by(ano_consolidacao, mes_consolidacao) %>% select(ano_consolidacao, mes_consolidacao) %>% distinct
# for(consolidar in a_consolidar) {
#   message(consolidar)
#   #message(consolidar)
#   #message(paste('Consolidando', consolidar$ano_consolidacao, '-', consolidar$mes_consolidacao))
# }
