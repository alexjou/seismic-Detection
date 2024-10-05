from flask import Flask, render_template, request
import pandas as pd
import plotly.express as px
import scipy.signal as signal
import plotly.graph_objects as go

app = Flask(__name__)

def generate_graphs(missao):
    try:
        df = pd.read_csv(f"{missao}_data.csv", index_col=0)
    except FileNotFoundError:
        return None, None, None, None, None

    # Remover espaços em branco das colunas
    df.columns = df.columns.str.strip()

    # Converter a coluna 'time_abs' para datetime
    df['time_abs'] = pd.to_datetime(df['time_abs(%Y-%m-%dT%H:%M:%S.%f)'])

    # Aplicar o filtro passa-baixa aos dados 'time_rel(sec)'
    cutoff_freq = 0.1  # frequência de corte
    sampling_rate = 1  # taxa de amostragem
    b, a = signal.butter(4, cutoff_freq, btype='low', fs=sampling_rate)
    df['filtered_time_rel'] = signal.filtfilt(b, a, df['time_rel(sec)'])

    # Detectar picos no sinal original
    peaks_original, _ = signal.find_peaks(df['time_rel(sec)'], height=5000)  # ajustar altura conforme necessário

    # Detectar picos no sinal filtrado
    peaks_filtered, _ = signal.find_peaks(df['filtered_time_rel'], height=5000)  # ajustar altura conforme necessário

    # Gráfico 1: Gráfico de Barras dos Tipos de MQ, somente se mq_type existir
    fig_bar = None
    if 'mq_type' in df.columns:
        mq_counts = df['mq_type'].value_counts().reset_index()
        mq_counts.columns = ['mq_type', 'count']
        fig_bar = px.bar(mq_counts, x='mq_type', y='count',
                         title='Contagem de Tipos de MQ', labels={'mq_type': 'Tipo de MQ', 'count': 'Contagem'})

    # Gráfico combinado: Sinal Original, Sinal Filtrado e Picos Detectados
    fig_combined = go.Figure()

    # Adicionar o sinal original
    fig_combined.add_trace(go.Scatter(x=df['time_abs'], y=df['time_rel(sec)'], mode='lines', name='Sinal Original', line=dict(color='blue')))

    # Adicionar o sinal filtrado
    fig_combined.add_trace(go.Scatter(x=df['time_abs'], y=df['filtered_time_rel'], mode='lines', name='Sinal Filtrado', line=dict(color='red')))

    # Adicionar os picos detectados do sinal original
    fig_combined.add_trace(go.Scatter(x=df['time_abs'].iloc[peaks_original], y=df['time_rel(sec)'].iloc[peaks_original], 
                                       mode='markers', name='Picos Originais', marker=dict(color='darkblue', size=10, symbol='x')))

    # Adicionar os picos detectados do sinal filtrado
    fig_combined.add_trace(go.Scatter(x=df['time_abs'].iloc[peaks_filtered], y=df['filtered_time_rel'].iloc[peaks_filtered], 
                                       mode='markers', name='Picos Filtrados', marker=dict(color='yellow', size=10, symbol='x')))

    # Configurando o layout do gráfico combinado
    fig_combined.update_layout(
        title='Sinal Original vs. Sinal Filtrado e Detecção de Picos',
        xaxis_title='Tempo Absoluto',
        yaxis_title='Tempo Relativo (segundos)',
        legend_title='Sinais',
        xaxis=dict(tickformat='%Y-%m-%d', tickangle=45),  # Formatação do eixo X
        autosize=True
    )

    # Geração das tabelas
    all_data_html = df.to_html(classes='data', header="true", index=True)
    
    # Captura os dados dos picos filtrados (limitando a 5 resultados)
    filtered_peak_indices = peaks_filtered[:5]  # Pega os primeiros 5 índices de picos filtrados
    filtered_peak_data = df.iloc[filtered_peak_indices]  # Acessa os dados correspondentes
    filtered_data_html = filtered_peak_data[['time_abs', 'time_rel(sec)', 'filtered_time_rel']].to_html(classes='data', header="true", index=True)

    print("Todos os dados:")
    print(all_data_html)

    print("Dados filtrados dos picos:")
    print(filtered_data_html)

    return fig_bar, fig_combined, all_data_html, filtered_data_html

@app.route('/', methods=['GET', 'POST'])
def index():
    missao = request.form.get('missao', 'apollo')
    figs = generate_graphs(missao)
    
    if figs[0] is None:
        return render_template('index.html', error="Dados não encontrados para a missão selecionada.")
    
    graph_json = [fig.to_json() for fig in figs[:2] if fig is not None]  # Ajuste para retornar apenas os dois gráficos
    return render_template('index.html', graph_json=graph_json, table_all_data=figs[2], table_filtered_data=figs[3])

if __name__ == '__main__':
    app.run(debug=True)
