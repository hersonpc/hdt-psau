require(lubridate)
require(shiny)
ui <- fluidPage(
  headerPanel("PSAU 2- Pesquisa de Satisfação de Usuários"),
  sidebarPanel(
    selectInput("ANO", 'Selecione o Ano', rev(unique(df$geral$Consolidar.no.ano))),
    selectInput("MES", 'Selecione o Mês', months_full)
  ),
  mainPanel(
    tabsetPanel(
      tabPanel("Distribuição das amostras", 
               plotOutput('plot1')
      ),
      tabPanel("Anual", 
               tags$h3('Score de Satisfação Anual'),
               fluidRow(
                 column(6,
                        tableOutput('table2')
                 ),
                 column(6,
                        tableOutput('table1')
                 )
               )
      ),
      tabPanel("Mensal", "Visão mensal")
    )
  )
)
server <- function(input, output) {
  
  output$plot1 <- renderPlot({
    param.ano <- input$ANO
    data <- (df$geral %>% filter(Consolidar.no.ano == param.ano))
    plot(translateLikert(data$Infraestrutura..Segurança.), 
         main = paste("Histograma Satifação sobre Segurança em", param.ano),
         ylab = "Percentual de Satifação")
  })
  
  output$table1 <- renderTable({
    param.ano <- input$ANO
    param.mes <- input$MES
    data <- (df$geral %>% filter(Consolidar.no.ano == param.ano))
    tbl1 <- as.data.frame(table(data$Consolidar.no.mês, data$Infraestrutura..Segurança.))
    reshape2::dcast(tbl1, Var1 ~ Var2)
    # if(input$MES %in% months_full) {
    #   data <- (df$geral %>% filter(Consolidar.no.ano == param.ano & Consolidar.no.mês == param.mes))
    #   table(data$Consolidar.no.mês, data$Infraestrutura..Segurança.)
    # }
  })
  
  
  output$table2 <- renderTable({
    
    param.ano <- input$ANO
    satisfacao_df %>% 
      filter(year(PERIODO) == param.ano) %>%
      mutate(PERIODO = paste0(months[month(PERIODO)], '/', year(PERIODO)))
    
    # if(input$MES %in% months_full) {
    #   data <- (df$geral %>% filter(Consolidar.no.ano == param.ano & Consolidar.no.mês == param.mes))
    #   table(data$Consolidar.no.mês, data$Infraestrutura..Segurança.)
    # }
  })
  
}

shiny::runApp(host = '0.0.0.0')
shinyApp(ui = ui, server = server, )


############################################################################################################################################################
############################################################################################################################################################
############################################################################################################################################################
############################################################################################################################################################
############################################################################################################################################################
############################################################################################################################################################


require(tidyverse)
require(reshape2)

# setwd('F:/gdrive/code/isg/hdt/hdt-psau/source')

months <- c("Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez")
months_full <- c("Janeiro","Fevereiro","Março","Abril","Maio","Junho",
                 "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro")



read.psau.df <- function(source) {
  df <- 
    read.csv(source, stringsAsFactors = FALSE, encoding = 'UTF-8', na.strings = c("")) %>% 
    tbl_df()
}

loadPSAUDataset <- function() {
  url.geral <- "https://docs.google.com/spreadsheets/d/1R38ZhGubZsMR3LC5pPCmdvy857XnGIrga6RroxBZ3U0/pub?gid=1725198295&single=true&output=csv"
  url.ambulatorio <- "https://docs.google.com/spreadsheets/d/1Vq1QQUPtXRcqvOsB8pPHVKq9aLDTp5_4OBLT7N0yBl4/pub?gid=476331211&single=true&output=csv"
  
  df.geral <- read.psau.df(url.geral)
  df.amb <- read.psau.df(url.ambulatorio)
  
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
  output <- 
    data %>% 
    mutate(
      ANO = Consolidar.no.ano,
      MES = factor(Consolidar.no.mês, levels = months_full),
      NOTA = Nota.da.escala.de.0.a.10,
      CLASSE = ifelse(NOTA <= 6, 'Detrator', ifelse(NOTA >= 9, 'Promoter', 'Neutro')),
      NPS = ifelse(NOTA <= 6, -1, ifelse(NOTA >= 9, 1, 0))
    ) %>%
    select(ANO, MES, ID, NOTA, CLASSE, NPS) %>%
    filter(!is.na(NOTA)) %>%
    group_by(ANO, MES) %>%
    summarise(QTDE_FORM = n(), NPS_SCORE = sum(NPS), PROP = paste0(round((NPS_SCORE / QTDE_FORM) *100, 1), '%'))
  
  return(output)
}

comparacaoNPS <- function(data) {
  
  data <-
    rbind(
      df$geral %>%
        mutate(
          ANO = Consolidar.no.ano, 
          MES = factor(Consolidar.no.mês, levels = months_full),
          PERIODO = factor(paste0(ANO, '/', MES), levels = paste0(periodos$ANO,'/',periodos$MES)),
          ID = paste0('G.', ID),
          NOTA = Nota.da.escala.de.0.a.10) %>%
        filter(ANO == 2019, MES %in% resumo$MES) %>%
        select(PERIODO, ID, NOTA) %>%
        filter(!is.na(NOTA))
      ,
      df$ambulatorio %>%
        mutate(
          ANO = Consolidar.no.ano, 
          MES = factor(Consolidar.no.mês, levels = months_full),
          PERIODO = factor(paste0(ANO, '/', MES), levels = paste0(periodos$ANO,'/',periodos$MES)),
          ID = paste0('A.', ID),
          NOTA = Nota.da.escala.de.0.a.10) %>%
        filter(ANO == 2019, MES %in% resumo$MES) %>%
        select(PERIODO, ID, NOTA) %>%
        filter(!is.na(NOTA))
    )
  
  output <- 
    data %>% 
    mutate(
      CLASSE = ifelse(NOTA <= 6, 'Detrator', ifelse(NOTA >= 9, 'Promoter', 'Neutro')),
      NPS = ifelse(NOTA <= 6, -1, ifelse(NOTA >= 9, 1, 0))
    ) %>%
    filter(!is.na(NOTA), !is.na(PERIODO))
  
  output %>% 
    group_by(PERIODO) %>%
    summarise(DETRATORES = sum(ifelse(CLASSE == 'Detrator', 1, 0)),
              NEUTRO = sum(ifelse(CLASSE == 'Neutro', 1, 0)),
              PROMOTORES = sum(ifelse(CLASSE == 'Promoter', 1, 0))) %>%
    melt() %>%
    ggplot(aes(x = PERIODO, y = value, fill = variable)) +
    geom_col(show.legend = FALSE) + 
    geom_text( aes(label = value), vjust = -1.1 ) +
    facet_wrap(~variable) +
    scale_y_continuous(limits = c(0, 400)) +
    theme_bw() + 
    labs(title = "NPS Composição",
         x = "",
         y = "\nNumero absoluto\n",
         caption = "Fonte: PSAU HDT\nDados consolidados em 19/03/2020 11:00:13")
  
  table(output$PERIODO, output$CLASSE)
  return(output)
}

satisfacao.recepcao <- function(data) {
  
satisfacao_df <- 
  df$geral %>% 
  # filter(Consolidar.no.ano >= 2019) %>% # & Consolidar.no.mês == "Agosto") %>%
  mutate(
    ANO = Consolidar.no.ano,
    MES = Consolidar.no.mês,
    PERIODO = ymd(paste0(ANO, '/', MES, '/01')),
    S01 = translateLikert(Recepção..Atend..da.recepção.),
    S02 = translateLikert(Médico..Atendimento.dos.médicos.),
    S03 = translateLikert(Enfermagem..Atend..da.enfermagem.),
    S04 = translateLikert(Serviço.Social..Atend..do.Serviço.Social.),
    S05 = translateLikert(Pscicologia..Atend..da.Pscicologia.),
    S06 = translateLikert(Nutrição..Atend..da.Nutrição.),
    S07 = translateLikert(Reabilitação..Atend..da.Fisioterapia.),
    S08 = translateLikert(Reabilitação..Atend..da.Terapia.Ocupacional.),
    S09 = 0,
    S10 = translateLikert(Infraestrutura..Recepção.),
    S11 = translateLikert(Infraestrutura..Segurança.),
    S12 = translateLikert(Infraestrutura..Limpeza.),
    S13 = translateLikert(Infraestrutura..Enxoval..lençois..toalhas..etc.....),
    SGERAL = S01 + S02 + S03 + S04 + S05 + S06 + S07 + S08 + S09 + S10 + S11 + S12 + S13,
    QTD_RESP = 
      ifelse(S01 > 0, 1, 0) + ifelse(S02 > 0, 1, 0) + ifelse(S03 > 0, 1, 0) + ifelse(S04 > 0, 1, 0) +
      ifelse(S05 > 0, 1, 0) + ifelse(S06 > 0, 1, 0) + ifelse(S07 > 0, 1, 0) + ifelse(S08 > 0, 1, 0) +
      ifelse(S09 > 0, 1, 0) + ifelse(S10 > 0, 1, 0) + ifelse(S11 > 0, 1, 0) + ifelse(S12 > 0, 1, 0) +
      ifelse(S13 > 0, 1, 0),
    SATISFACAO = ifelse(QTD_RESP > 0, SGERAL / QTD_RESP, 0),
    S = ifelse(SATISFACAO >= 0.8, 'BOM/OTIMO', ifelse(SATISFACAO == 0, 'NULO', 'BAIXO'))
  ) %>%
  select(PERIODO,
         S01:S
         ) %>% #View
    group_by(PERIODO) %>%
    summarise(QTDE = n(), TOTAL_SATISFACAO = sum(SATISFACAO), MEDIA = mean(SATISFACAO), MEDIANA = median(SATISFACAO))
  
  translateLikert(unique(df$geral$Recepção..Atend..da.recepção.))
    
  #output <- 
    df$ambulatorio %>% 
    mutate(
      ANO = Consolidar.no.ano,
      MES = factor(Consolidar.no.mês, levels = months_full),
      RECEPCAO = translateLikert(Ambulatório..Atendimento.da.recepção.),
      MEDICO = translateLikert(Ambulatório..Atendimento.dos.médicos.),
      SATISFACAO = ifelse(RECEPCAO > 0 & MEDICO > 0, (RECEPCAO + MEDICO) / 2, 
                     ifelse(RECEPCAO > 0, RECEPCAO, 
                            ifelse(MEDICO > 0, MEDICO, 0))),
      NPS = ifelse(is.na(Nota.da.escala.de.0.a.10), 0, # NEUTROS
                   ifelse(Nota.da.escala.de.0.a.10 <= 6, -1, # DETRETORES
                          ifelse(Nota.da.escala.de.0.a.10 >= 9, 1, 0)) # PROMOTERS
                   )
    ) %>%
    filter(ANO >= 2019) %>%
    select(ANO, MES, ID, 
           ATENDENTE,
           RECEPCAO, 
           MEDICO,
           SATISFACAO,
           #ATENDENTE = ifelse(is.na(ATENDENTE), NA, stringr::str_trim(ATENDENTE)), 
           NPS
           )
  
  Z#output <- 
    df$ambulatorio %>% 
    mutate(
      ANO = Consolidar.no.ano,
      MES = factor(Consolidar.no.mês, levels = months_full),
      NOTA_RECEPCAO = factor(Ambulatório..Atendimento.da.recepção., levels = c("Não se aplica", "Péssimo", "Ruim", "Regular", "Bom", "Ótimo")),
      SCORE_RECEPCAO = ifelse(NOTA_RECEPCAO == "Péssimo", 0.2,
                     ifelse(NOTA_RECEPCAO == "Ruim", 0.4,
                            ifelse(NOTA_RECEPCAO == "Regular", 0.6,
                                   ifelse(NOTA_RECEPCAO == "Bom", 0.8,
                                          ifelse(NOTA_RECEPCAO == "Ótimo", 1, 0))))),
      BOM_OTIMO = ifelse(NOTA_RECEPCAO == "Bom", 1, ifelse(NOTA_RECEPCAO == "Ótimo", 1, 0))
    ) %>%
    filter(ANO >= 2019) %>%
    select(ANO, MES, ID, NOTA, SCORE, BOM_OTIMO) %>%
    filter(!is.na(NOTA) & SCORE > 0) %>%
    group_by(ANO, MES) %>%
    summarise(N_RESPOSTAS = n(), 
              BOM_OTIMO = sum(BOM_OTIMO),
              SCORE_TOTAL = sum(SCORE), 
              FREQ = round((SCORE_TOTAL / N_RESPOSTAS) *100, 1),
              PERDA = 100 - FREQ,
              PROP = paste0(FREQ, '%')
              ) %>%
    ungroup()
    
  
  output <- 
    mutate(output,
           PERIODO = factor(paste0(ANO, '/', MES), levels = paste0(output$ANO,'/',output$MES)) 
           )
  return(output)
}

df <- loadPSAUDataset()

resumo <- data.frame(ANO = c(2019), MES = c("Outubro", "Novembro", "Dezembro"))
periodos <- data.frame(ANO = c(rep(2019, 12), rep(2020, 12)), MES = months_full)
tabelaNPS(df$ambulatorio) %>%
  mutate(
    PERIODO = factor(paste0(ANO, '/', MES), levels = paste0(resumo$ANO,'/',resumo$MES))
  ) %>%
  ggplot(aes(x = PERIODO, y = NPS_SCORE)) +
  geom_col(show.legend = FALSE) +
  theme_bw() +
  labs(title = "NPS Ambulatório",
       x = "", #  "\nPeríodo\n",
       y = "\nScore NPS\n")

satisfacao.recepcao(df$ambulatorio) %>%
  filter(ANO >= 2019) %>%
  select(PERIODO, FREQ, PERDA) %>% melt() %>%
  mutate(variable = factor(variable, levels = c("PERDA", "FREQ") )) %>%
  ggplot(aes(x = PERIODO, y = value, fill = variable)) +
  geom_bar(position = "fill", stat = "identity", show.legend = FALSE) +
  scale_y_continuous(labels = scales::percent_format()) +
  theme_bw() +
  labs(title = "Satisfação Ambulatório - Atendimento da Recepção",
       x = "", #  "\nPeríodo\n",
       y = "\nScore NPS\n")


library(plotly)
df2 <- satisfacao.recepcao(df$ambulatorio) %>%
  filter(ANO >= 2019) %>%
  select(PERIODO, FREQ, PERDA) %>% melt() %>%
  mutate(variable = factor(variable, levels = c("PERDA", "FREQ") ))
plot_ly(
  x = df$PERIODO,
  y = df$value,
  name = "SF Zoo",
  type = "bar"
)
  
table(df$ambulatorio$Ambulatório..Atendimento.da.recepção.)


# NOTA_MEDICO = Ambulatório..Atendimento.dos.médicos.#,
