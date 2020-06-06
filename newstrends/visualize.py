# AUTOGENERATED! DO NOT EDIT! File to edit: 03_visualize.ipynb (unless otherwise specified).

__all__ = ['visualizer', 'visualizer']

# Cell
from newstrends import loader, describe
import pandas as pd
import datetime, os
from datetime import timezone
import matplotlib.pyplot as plt

# Cell
import statsmodels.api as sm
from statsmodels.tsa.api import VAR
from pmdarima import auto_arima
import numpy as np

import warnings
warnings.filterwarnings("ignore")


# Cell
class visualizer:
    "my visualizer! Don't know what I'm doing with it yet though"

    def __init__(self, coverageTrendsPath=".", workdir = "docs"):
        """ initializing building a list of all the pkls in workdir"""
        self.coverageTrendsPath = coverageTrendsPath
        self.workdir = workdir

        os.makedirs(workdir, exist_ok=True)

        self.colors = ["orange", "green", "red", "brown", "blue", "yellow", "pink"]


    def runDefault(self):

        outdir=self.workdir

        publisherList = ["newyorktimes", "washingtonpost"]

        describer = describe.describer()

        describer.set_articleDir(path=self.coverageTrendsPath)
        describer.load_articles(publications=publisherList, lastN=5)
        describer.fitVectorizer(ngram_range=(1,1))

        topN = pd.DataFrame()

        for publisher in publisherList:
            topN[publisher] = [x[0] for x in describer.getTopNWords(10, source=[publisher])]

        vcs = topN.melt(var_name='publisher', value_name='words')["words"].value_counts()
        myTime = datetime.datetime.now(tz=timezone.utc).strftime('%Y%m%d-%H%M')
        myTime = myTime[:-1]
        myTime +="0"
        plt.close('all') #in case of zombies or something
        os.makedirs("{}/img".format(outdir), exist_ok=True)
        os.makedirs("{}/timeseries".format(outdir), exist_ok=True)

        df = describer.df

        """
        If I remember what this is doing, I'm using counter to find signifcant terms, then going and grpahing
        them, saving the time series in a pkl in outdir;

        The thing is, the way I'm building this, I want to use pip to import to the CoverageTrends folder, so
        path should be "." and not "../CoverageTrends as I'm doing here; so what I want is visualzier to have
        a path to coverage_trends!"
        """
        for middleWord in vcs.dropna().index: #k, this is going to be wayyy too many images, but just testing

            tmp = df[df["tokens"].apply(lambda x: (middleWord in x))].copy().fillna(0)
            tmp.date = pd.to_datetime(tmp.date)
            tmp = tmp.groupby(["source", "date"]).count()["quickReplace"]
            try:  #for some reason, sometimes the formatting's getting messed up
                tmp.unstack(level=0).fillna(0).to_pickle("{}/timeseries/{}.pkl".format(outdir, middleWord))
            except:
                pass
            ax = tmp.unstack(level=0).fillna(0).plot(title="Frontpage mentions of {}".format(middleWord), figsize=(8,8))
            ax.set_ylabel("frontpage mentions at time")
            try:
                deleteMe = [oldFile for oldFile in os.listdir("{}/img".format(outdir)) if oldFile.endswith(middleWord+".jpg")]
                for oldFile in deleteMe:
                    os.remove("{}/img/{}".format(outdir, oldFile))
            except:
                pass

            ax.figure.savefig("{}/img/{}_{}.jpg".format(outdir, myTime, middleWord))
            plt.close('all') #close all figures


# Cell
class visualizer(visualizer):
    " build models for time series as done from CoverageTrends "

    def buildModels(self, verbose=False):

        workdir = self.workdir

        self.targetPaths = []

        for filename in os.listdir("{}/timeseries".format(workdir)):
            if filename.endswith(".pkl"):
                self.targetPaths.append("{}/timeseries/{}".format(workdir, filename))

        if verbose:
            print(self.targetPaths)
        """ build a model for each target in targetPaths using fnc """
        for target in self.targetPaths:
            print(target)
            try:
                df = pd.read_pickle(target)
                self.buildQuickVAR(df, target.split("/")[-1][:-4])
                if verbose:
                    print("var done")
                myFreq = "3h"
                self.buildQuickSARIMAX(df.resample(myFreq).mean().fillna(0), target.split("/")[-1][:-4], freq=8)
                #os.remove("{}".format(target))
            except:
                pass


    def buildQuickVAR(self, df, name, test_size=-1, validation_size=-1):
        """ builds VAR model for series """
        os.makedirs("{}/models/VAR".format(self.workdir), exist_ok=True)

        #Fit model
        model = VAR(df)
        results = model.fit(maxlags=24, ic='aic')

        #Get forecast
        lag_order = results.k_ar
        newVals = pd.DataFrame(results.forecast(df.values[-lag_order:], 24))
        newVals.index = [df.index.max()+datetime.timedelta(minutes=30*x) for x in range(1,25)]
        newVals.columns = df.columns
        newVals = results.fittedvalues.append(newVals)

        #plot
        ax = newVals.plot(style=":", figsize=(8,8), color=self.colors, title="VAR Quick Fit for {}".format(name))
        df.plot(ax=ax, color=self.colors, legend=False)

        ax.figure.savefig("{}/models/VAR/{}.jpg".format(self.workdir, name))
        plt.close('all') #close all figures

    def buildQuickSARIMAX(self, df, name, freq=24, test_size=-1, validation_size=-1):
        """ takes dataframe of time series and builds a SARIMAX model for each column """
        """ seasonality is daily for now, which is 48 time step thingies"""
        """ for now, just fiting to training data; will truncate last day starting next week for testing as well"""

        os.makedirs("{}/SARIMAX".format(self.workdir), exist_ok=True)

        """
        k, doing this at the 30 minute aggregate is WAY too slow, so resampling hour
        """

        corr_df = df.copy()
        for i in range(1,13):
            corr_df = pd.concat([corr_df, df.diff(i).add_prefix("L{}_".format(i))], axis=1)

        corr_df = np.abs(corr_df)
        corr_df = corr_df.dropna().corr()[df.columns][len(df.columns):]

        #since I generated this, I might as well save it to a csv (js can't read pkl)
        os.makedirs("{}/models/{}".format(self.workdir, "corr"), exist_ok=True)
        corr_df.to_csv("{}/models/{}/{}.csv".format(self.workdir, "corr", name))

        max_lag = -1
        results_df = df.copy()

        print(name)

        #plot SARIMAX using best correlating lag of an exogenous
        #does some magic to do a bunch of forecasts
        #I probably should be measuring errors =/
        for column in df.columns:
            #get max lag - we'll plot them all together so the maxlag is going to be the max_lag
            best_series = corr_df[corr_df.index.map(lambda x: not x.endswith(column))][column].idxmax()
            lag = int(best_series.split("_")[0][1:])
            if lag > max_lag:
                max_lag = lag

            exog = best_series.split("_")[1]

            endogenous = df[[column]][lag:].copy()
            exogenous = df[[exog]].shift(lag)[lag:]
            model = auto_arima(endogenous, exogenous=exogenous, scoring="mae", out_of_sample_size=freq, m=freq, stepwise=True)
            endogenous[column]=model.predict_in_sample(exogenous=exogenous)
            forecasts = pd.DataFrame()
            forecasts[column] = model.predict(n_periods=lag, exogenous=df[[exog]][-lag:])
            forecasts.index = [endogenous.index[-1] + x*endogenous.index[-1].freq for x in range(1,lag+1)]
            endogenous = endogenous.append(forecasts)
            while results_df.index.max() < endogenous.index.max():
                results_df = results_df.append(pd.Series(name=results_df.index[-1] + results_df.index[-1].freq))
            results_df[column] = endogenous[column]

        ax = results_df[max_lag:].plot(legend=False, style=":", color=self.colors, title=name, figsize=(8,8))
        df.plot(ax=ax, style="-", color=self.colors, legend=True)

        ax.figure.savefig("{}/models/SARIMAX/{}.jpg".format(self.workdir, name))
        plt.close('all') #close all figures
