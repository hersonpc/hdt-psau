require(tidyverse)
require(reshape2)
require(tidyr)
require(dplyr)
require(lubridate)
library(grid)
library(gridExtra)

setwd('Z:/code/isg/hdt/hdt-psau/source')

months <- c("Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez")
months_full <- c("Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                 "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro")
calendario <- 
  data.frame(ANO = rep(seq(2018, year(now())), times = 1, each = 12),
             MES = factor(months_full, levels = months_full),
             MES_CURTO = months,
             SEMESTRE = c(rep('1º sim',6), rep('2º sim',6)),
             ID_TRIMESTRE = c(rep('.Q1',3), rep('.Q2',3), rep('.Q3',3), rep('.Q4',3)),
             TRIMESTRE = c(rep('1º tri',3), rep('2º tri',3), rep('3º tri',3), rep('4º tri',3)),
             BIMESTRE = c(rep('1º bim',2), rep('2º bim',2), rep('3º bim',2), rep('4º bim',2), rep('5º bim',2), rep('6º bim',2))
  ) %>%
  mutate(ID_TRIMESTRE = paste0(ANO, ID_TRIMESTRE),
         PERIODO = paste0(ANO, '/', MES),
         PERIODO_CURTO = paste0(MES_CURTO, '/', ANO)
         # PERIODO_CURTO = paste0(substr(as.character(ANO), 3, 4), '/', MES_CURTO)
         )
calendario$PERIODO <- factor(calendario$PERIODO, levels = calendario$PERIODO)
calendario$PERIODO_CURTO <- factor(calendario$PERIODO_CURTO, levels = calendario$PERIODO_CURTO)



getDataPSAU <- function(url) {
  df <- 
    read.csv(url, stringsAsFactors = FALSE, encoding = 'UTF-8', na.strings = c("")) %>% 
    tbl_df()
}

loadPSAU <- function() {
  url.geral <- "https://docs.google.com/spreadsheets/d/1R38ZhGubZsMR3LC5pPCmdvy857XnGIrga6RroxBZ3U0/pub?gid=1725198295&single=true&output=csv"
  url.ambulatorio <- "https://docs.google.com/spreadsheets/d/1Vq1QQUPtXRcqvOsB8pPHVKq9aLDTp5_4OBLT7N0yBl4/pub?gid=476331211&single=true&output=csv"
  
  df.geral <- getDataPSAU(url.geral)
  df.amb <- getDataPSAU(url.ambulatorio)
  
  return(list(
    geral = df.geral,
    ambulatorio = df.amb
  ))
}

translateLikert <- function(likertValue) {
  likertValue <- as.character(likertValue)
  translated <- ifelse(likertValue == "Péssimo", 0.2,
                       ifelse(likertValue == "Ruim", 0.4,
                              ifelse(likertValue == "Regular", 0.6,
                                     ifelse(likertValue == "Bom", 0.8,
                                            ifelse(likertValue == "Ótimo", 1, 0)))))
  return(translated)
}

tabelaNPS <- function(data) {
  
  nps.ambulatorio <- 
    data$ambulatorio %>% 
    mutate(
      ORIGEM = 'AMBULATORIO',
      ANO = Consolidar.no.ano,
      MES = Consolidar.no.mês, #factor(Consolidar.no.mês, levels = months_full),
      NOTA = Nota.da.escala.de.0.a.10,
      CLASSE = ifelse(NOTA <= 6, 'Detrator', ifelse(NOTA >= 9, 'Promoter', 'Neutro')),
      NPS = ifelse(NOTA <= 6, -1, ifelse(NOTA >= 9, 1, 0))
    ) %>%
    select(ANO, MES, ORIGEM, ID, NOTA, CLASSE, NPS) %>%
    filter(!is.na(NOTA))
  
  nps.geral <-
    data$geral %>% 
    mutate(
      ORIGEM = 'GERAL',
      ANO = Consolidar.no.ano,
      MES = Consolidar.no.mês, #factor(Consolidar.no.mês, levels = months_full),
      NOTA = Nota.da.escala.de.0.a.10,
      CLASSE = ifelse(NOTA <= 6, 'Detrator', ifelse(NOTA >= 9, 'Promoter', 'Neutro')),
      NPS = ifelse(NOTA <= 6, -1, ifelse(NOTA >= 9, 1, 0))
    ) %>%
    select(ANO, MES, ORIGEM, ID, NOTA, CLASSE, NPS) %>%
    filter(!is.na(NOTA))
  
  nps.df <-
    left_join(
      rbind(nps.ambulatorio, nps.geral), 
      calendario %>% mutate(MES = as.character(MES)), 
      by = c("ANO" = "ANO", "MES" = "MES")) 
  
  
  output <- 
    nps.df %>%
    group_by(PERIODO_CURTO) %>%
    summarise(QTDE_FORM = n(), 
              QTDE_GERAL = sum(ifelse(ORIGEM == "GERAL", 1, 0)),
              QTDE_AMBULATORIO = sum(ifelse(ORIGEM == "AMBULATORIO", 1, 0)),
              NPS_SCORE = sum(NPS), 
              PROP = paste0(round((NPS_SCORE / QTDE_FORM) *100, 1), '%')
              )
  
  return(list(df = nps.df, 
              consolidado = output))
}

plotNPStoPNG <- function(nps.df, consulta_trimestre, to_file = FALSE) {
  # consulta_trimestre <- "2020.Q1"
  referencia <- 
    calendario %>% 
    filter(ID_TRIMESTRE == consulta_trimestre)
  #filter(ANO >= 2019)
  
  nps.consolidado <- 
    nps.df %>% 
    filter(ID_TRIMESTRE == consulta_trimestre) %>%
    #filter(ANO >= 2019) %>%
    group_by(PERIODO = PERIODO_CURTO) %>%
    summarise(DETRATORES = sum(ifelse(CLASSE == 'Detrator', 1, 0)),
              NEUTRO = sum(ifelse(CLASSE == 'Neutro', 1, 0)),
              PROMOTORES = sum(ifelse(CLASSE == 'Promoter', 1, 0)),
              TOTAL = n(),
              P_DETRATORES = round((DETRATORES *100) / TOTAL),
              P_NEUTRO = round((NEUTRO *100) / TOTAL),
              P_PROMOTORES = round((PROMOTORES *100) / TOTAL),
              NPS = P_PROMOTORES - P_DETRATORES,
              ZONA = ifelse(NPS > 75, "ZONA DE EXCELENCIA",
                            ifelse(NPS > 50, "ZONA DE QUALIDADE",
                                   ifelse(NPS > 0, "ZONA DE APERFEIÇOAMENTO", "ZONA CRÍTICA")
                            )
              )
    )
  
  output.plot1 <-
    nps.consolidado %>%
    select(PERIODO, NPS) %>%
    melt(id = "PERIODO") %>%
    ggplot(aes(x = PERIODO, y = value)) +
    geom_point(show.legend = FALSE, col = 1, size = 3) +
    geom_text( aes(label = value), vjust = -1.1, size = 5, col = 1) +
    scale_y_continuous(limits = c(-100, 110)) +
    geom_rect(aes(xmin = -Inf, xmax = Inf, ymin = -100, ymax=0), alpha = 0.05, fill="red", show.legend = F) +
    geom_rect(aes(xmin = -Inf, xmax = Inf, ymin = 0, ymax=50), alpha = 0.05, fill="yellow", show.legend = F) +
    geom_rect(aes(xmin = -Inf, xmax = Inf, ymin = 50, ymax=75), alpha = 0.05, fill="#2fd1ed", show.legend = F) +
    geom_rect(aes(xmin = -Inf, xmax = Inf, ymin = 75, ymax=100), alpha = 0.05, fill="green", show.legend = F) +
    # annotate(geom="text", x=0.55, y=-10, label="Crítico", color="black") +
    # annotate(geom="text", x=0.7, y=50, label="Aperfeiçoamento", color="black") +
    annotation_custom(grobTree(textGrob("Crítico", x=0.02,  y=.27, hjust=0,
                                        gp=gpar(col="#2b2d2e", fontsize=8, fontface="italic"))) ) +
    annotation_custom(grobTree(textGrob("Aperfeiçoamento", x=0.02,  y=.6, hjust=0,
                                        gp=gpar(col="#2b2d2e", fontsize=8, fontface="italic"))) )+
    annotation_custom(grobTree(textGrob("Qualidade", x=0.02,  y=.75, hjust=0,
                                        gp=gpar(col="#2b2d2e", fontsize=8, fontface="italic"))) )+
    annotation_custom(grobTree(textGrob("Excelência", x=0.02,  y=.86, hjust=0,
                                        gp=gpar(col="#2b2d2e", fontsize=8, fontface="italic"))) )+
    theme_light() +
    labs(subtitle = "Avaliação do NPS",
         # subtitle = "HDT - Hospital Estadual de Doenças Tropicais", 
         x = "",
         y = "\nPonturação\n")
  # y = "\nPonturação\n",
  # caption = paste0("Fonte: PSAU HDT\nTotal de pesquisas realizadas no periodo: ", sum(nps.consolidado$TOTAL),"\nDados processados em ", format.Date(Sys.time(), format = '%d/%m/%Y %H:%M:%S', tz = 'BR')))
  
  
  output.plot2 <-
    nps.consolidado %>%
    select(PERIODO:PROMOTORES) %>%
    melt(id = "PERIODO") %>%
    ggplot(aes(x = PERIODO, y = value, fill = variable)) +
    geom_col(show.legend = FALSE, col = 1) + 
    geom_text( aes(label = value), vjust = -1.1 ) +
    facet_wrap(~variable) +
    scale_fill_manual(values = c("#db1916", "#666666", "#3b940f")) +
    scale_y_continuous(limits = c(0, ceiling(max(nps.consolidado$TOTAL) * 1.1) )) +
    theme_light() + 
    theme(strip.background = element_rect(colour = "#666666", fill = "white"),
          strip.text.x = element_text(colour = "black", face = "bold")) +
    labs(subtitle = "Composição do NPS",
         x = "",
         y = "\nN. avaliações\n",
         caption = paste0("Fonte: PSAU HDT\nTotal de pesquisas realizadas no periodo: ", sum(nps.consolidado$TOTAL)))
  
  # output.plot <- 
  #   grid.arrange(
  #     textGrob(paste0("Hospital Estadual de Doenças Tropicais (HDT)\nAvaliação do Net Promoter Score de ", 
  #                     paste0(referencia[1,]$PERIODO_CURTO, ' à ', referencia[nrow(referencia),]$PERIODO_CURTO)), gp=gpar(fontsize=14,font=3)), 
  #     output.plot1, output.plot2,
  #      ncol = 1, nrow = 3, heights = c(.4, 2, 1.5),
  #      top = textGrob("Pesquisa de Satisfação do Usuário (PSAU)", gp=gpar(fontsize=20, font=2)),
  #      bottom = textGrob(paste0("Dados processados em ", format.Date(Sys.time(), format = '%d/%m/%Y %H:%M:%S', tz = 'BR')), 
  #                        gp=gpar(fontsize=8, font=1))
  #     )
  
  if(to_file) {
    outputDir <- file.path(getwd(), 'output')
    png_file <- file.path(outputDir, paste0('plot_nps_', consulta_trimestre,'_', format.Date(Sys.time(), format = '%Y-%m-%d', tz = 'BR'), '.png'))
    message(paste0('Gerando o plot no arquivo: ', png_file))
    png(png_file, 
        height=8, width=12, units = 'in', res = 300)
  }
  grid.arrange(
    textGrob(paste0("Hospital Estadual de Doenças Tropicais (HDT)\nAvaliação do Net Promoter Score de ", 
                    paste0(referencia[1,]$PERIODO_CURTO, ' à ', referencia[nrow(referencia),]$PERIODO_CURTO)), gp=gpar(fontsize=14,font=3)), 
    output.plot1, output.plot2,
    ncol = 1, nrow = 3, heights = c(.4, 2, 1.5),
    top = textGrob("Pesquisa de Satisfação do Usuário (PSAU)", gp=gpar(fontsize=20, font=2)),
    bottom = textGrob(paste0("Dados processados em ", format.Date(Sys.time(), format = '%d/%m/%Y %H:%M:%S', tz = 'BR')), 
                      gp=gpar(fontsize=8, font=1))
  )
  if(to_file) {
    dev.off()
  }
}


###################################################################################################
###################################################################################################
###################################################################################################
###################################################################################################
psau.df <- loadPSAU()


nps <- tabelaNPS(psau.df)

plotNPStoPNG(nps$df, "2019.Q3", T)
plotNPStoPNG(nps$df, "2019.Q4", T)
plotNPStoPNG(nps$df, "2020.Q1", T)
plotNPStoPNG(nps$df, "2020.Q2", F)
