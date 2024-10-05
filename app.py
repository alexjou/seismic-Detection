from flask import Flask, render_template, request
import pandas as pd
import plotly.express as px

app = Flask(__name__)

def generate_graphs(missao):
    try:
        df = pd.read_csv(f"{missao}_data.csv", index_col=0)
    except FileNotFoundError:
        return None, None, None, None, None, None, None
    
    # Filtra os dados dos eventos, se mq_type existir
    impact_events = deep_events = shallow_events = None
    if 'mq_type' in df.columns:
        impact_events = df[df['mq_type'] == 'impact_mq']
        deep_events = df[df['mq_type'] == 'deep_mq']
        shallow_events = df[df['mq_type'] == 'shallow_mq']

    # Gráfico 1: Histograma do Tempo Relativo
    fig_hist = px.histogram(df, x='time_rel(sec)', nbins=30, title='Distribuição do Tempo Relativo', 
                             labels={'time_rel(sec)': 'Tempo Relativo (segundos)'})
    
    # Gráfico 2: Linha do Tempo Absoluta
    df['time_abs'] = pd.to_datetime(df['time_abs(%Y-%m-%dT%H:%M:%S.%f)'])
    fig_line = px.line(df, x='time_abs', y='time_rel(sec)', title='Tempo Relativo por Tempo Absoluto', 
                       labels={'time_abs': 'Tempo Absoluto', 'time_rel(sec)': 'Tempo Relativo (segundos)'})
    
    # Gráfico 3: Gráfico de Barras dos Tipos de MQ, somente se mq_type existir
    fig_bar = None
    if 'mq_type' in df.columns:
        mq_counts = df['mq_type'].value_counts().reset_index()
        mq_counts.columns = ['mq_type', 'count']
        fig_bar = px.bar(mq_counts, x='mq_type', y='count',
                         title='Contagem de Tipos de MQ', labels={'mq_type': 'Tipo de MQ', 'count': 'Contagem'})
    
    # Gráfico 4: Dispersão entre Tempo Relativo e Tempo Absoluto, somente se mq_type existir
    fig_scatter = None
    if 'mq_type' in df.columns:
        fig_scatter = px.scatter(df, x='time_abs', y='time_rel(sec)', color='mq_type',
                                 title='Dispersão entre Tempo Absoluto e Tempo Relativo',
                                 labels={'time_abs': 'Tempo Absoluto', 'time_rel(sec)': 'Tempo Relativo (segundos)'})
    else:
        fig_scatter = px.scatter(df, x='time_abs', y='time_rel(sec)',
                                 title='Dispersão entre Tempo Absoluto e Tempo Relativo',
                                 labels={'time_abs': 'Tempo Absoluto', 'time_rel(sec)': 'Tempo Relativo (segundos)'})

    # Cálculos de média para cada tipo de evento, somente se mq_type existir
    average_time_impact = impact_events['time_rel(sec)'].mean() if impact_events is not None and not impact_events.empty else None
    average_time_deep = deep_events['time_rel(sec)'].mean() if deep_events is not None and not deep_events.empty else None
    average_time_shallow = shallow_events['time_rel(sec)'].mean() if shallow_events is not None and not shallow_events.empty else None

    return fig_hist, fig_line, fig_bar, fig_scatter, average_time_impact, average_time_deep, average_time_shallow

@app.route('/', methods=['GET', 'POST'])
def index():
    missao = request.form.get('missao', 'apollo')
    figs = generate_graphs(missao)
    
    if figs[0] is None:
        return render_template('index.html', error="Dados não encontrados para a missão selecionada.")
    
    graph_json = [fig.to_json() for fig in figs[:4] if fig is not None]
    averages = figs[4:]
    
    return render_template('index.html', graph_json=graph_json, averages=averages)

if __name__ == '__main__':
    app.run(debug=True)
