from flask import Flask , render_template
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from io import BytesIO
import base64

# word cloud library
from wordcloud import WordCloud

app = Flask(__name__)

playstore = pd.read_csv("data/googleplaystore.csv")

playstore.drop_duplicates(subset=['App'], keep='first',inplace=True)

# bagian ini untuk menghapus row 10472 karena nilai data tersebut tidak tersimpan pada kolom yang benar
playstore.drop([10472], inplace=True)

playstore['Category'] = playstore['Category'].astype('category')

playstore['Installs'] = playstore['Installs'].apply(lambda x: x.replace(",",""))
playstore['Installs'] = playstore['Installs'].apply(lambda x: x.replace("+",""))

# Bagian ini untuk merapikan kolom Size, Anda tidak perlu mengubah apapun di bagian ini
playstore['Size'].replace('Varies with device', np.nan, inplace = True ) 
playstore.Size = (playstore.Size.replace(r'[kM]+$', '', regex=True).astype(float) * \
             playstore.Size.str.extract(r'[\d\.]+([kM]+)', expand=False)
            .fillna(1)
            .replace(['k','M'], [10**3, 10**6]).astype(int))
playstore['Size'].fillna(playstore.groupby('Category')['Size'].transform('mean'),inplace = True)

playstore.Price = playstore.Price.apply(lambda x: x.replace("$", ""))
playstore.Price = playstore.Price.astype('float64')

# Ubah tipe data Reviews, Size, Installs ke dalam tipe data integer
playstore[['Reviews','Size','Installs']] = playstore[['Reviews','Size','Installs']].astype('int64')

print(playstore.dtypes)

@app.route("/")

def index():
    df2 = playstore.copy()

    # Statistik
    top_category = pd.crosstab(
        index=df2['Category'],
        columns='Jumlah',
    ).sort_values("Jumlah", ascending=False).reset_index()

    pd.set_option('display.float_format', lambda x: '%.1f' % x)

    rev_table = df2.groupby(['Category','App']).agg({
        'Reviews' : 'mean',
        'Rating' : 'mean'
    }).sort_values("Reviews",ascending=False).reset_index().head(10)
    #Dictionary stats digunakan untuk menyimpan beberapa data yang digunakan untuk menampilkan nilai di value box dan tabel
    stats = {
        'most_categories' : top_category['Category'][0],
        'total': top_category['Jumlah'][0],
        'rev_table' : rev_table.to_html(classes=['table thead-light table-striped table-bordered table-hover table-sm'])
    }

    cat_order = df2.groupby('Category').agg({'App' : 'count'}).sort_values('App', ascending=False).head()
    cat_order

    ######## Bar Plot ########
    cat_order = df2.groupby('Category').agg({
    'App' : 'count'
    }).rename({'Category':'Total'}, axis=1).sort_values('App', ascending=False).head()
    X = cat_order.index
    Y = cat_order['App']
    my_colors = 'rgbkymc'
    # bagian ini digunakan untuk membuat kanvas/figure
    fig = plt.figure(figsize=(8,3),dpi=300)
    fig.add_subplot()
    # bagian ini digunakan untuk membuat bar plot
    plt.barh(X, Y, color = (0.7,0.1,0.5,0.6))
    # bagian ini digunakan untuk menyimpan plot dalam format image.png
    plt.savefig('cat_order.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    # variabel result akan dimasukkan ke dalam parameter di fungsi render_template() agar dapat ditampilkan di 
    # halaman html
    result = str(figdata_png)[2:-1]


     ## Scatter Plot
    X = df2['Reviews'].values # axis x
    Y = df2['Rating'].values # axis y
    area = playstore['Installs'].values/10000000 # ukuran besar/kecilnya lingkaran scatter plot
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()
    # isi nama method untuk scatter plot, variabel x, dan variabel y
    plt.scatter(x=X,y=Y, s=area, alpha=0.3)
    plt.xlabel('Reviews')
    plt.ylabel('Rating')
    plt.savefig('rev_rat.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result2 = str(figdata_png)[2:-1]

    ## Histogram Size Distribution
    X=(df2['Size']/1000000).values
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()
    plt.hist(X,bins=100, density=True,  alpha=0.75)
    plt.xlabel('Size')
    plt.ylabel('Frequency')
    plt.savefig('hist_size.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    result3 = str(figdata_png)[2:-1]


    # filter only social
    social = (playstore['Category'] == 'SOCIAL')
    playSosial = playstore[social]

    # Group By with mean aggregasi
    listOfCat = playSosial.groupby(['Category','App']).agg({
    'Rating' : 'mean'
    }).sort_values("Rating",ascending=False).reset_index().head(10)

    # Create bars and choose color
    height = listOfCat['Rating']
    bars = listOfCat['App']
    x_pos = listOfCat['App']
    plt.figure(figsize=(20,5))
    plt.bar(x_pos, height, color = (0.7,0.1,0.5,0.6))

    plt.title('TOP SOCIAL RATING')
    plt.xlabel('App')
    plt.ylabel('Rating')
    plt.savefig('rating_social.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    topSocial = str(figdata_png)[2:-1]


    # Paid Apps Only with pie percentage
    #filter
    paided = playstore[playstore['Type'] == 'Paid']

    df3 = paided['Category'].value_counts()
    df3 = df3.reset_index()
    df3 = df3[:10]
    plt.figure(figsize=(10,5))
    plt.pie(x = list(df3['Category']), labels=list(df3['index']), autopct='%1.0f%%', pctdistance=0.8, labeldistance=1.2)
    plt.title('% Distribution of Paided Apps Categories')
    plt.savefig('pie_paid.png',bbox_inches="tight")

    figfile = BytesIO()
    plt.savefig(figfile, format='png')
    figfile.seek(0)
    figdata_png = base64.b64encode(figfile.getvalue())
    piePaid = str(figdata_png)[2:-1]
    
    # Tambahkan hasil result plot pada fungsi render_template()
    return render_template('index.html', stats=stats, result=result, result2=result2, result3=result3, topSocial=topSocial, piePaid=piePaid)

if __name__ == "__main__": 
    app.run(debug=True)