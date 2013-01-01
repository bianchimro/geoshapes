import sys
from sklearn import linear_model
from sklearn import cross_validation
from sklearn import metrics


ACTIVE_REGRESSION_MODELS = ['LinearRegressionModel']


def get_regression_class(class_name):
    cls = getattr(sys.modules[__name__], class_name)
    return cls


class BaseRegressionModel(object):

    regression_model = None
    
    def __init__(self, **options):
        self.options = options
    
    def train(self, x_data, y_data):
        raise NotImplementedError()
        
    def cv_score(self, x_data, y_data):
        raise NotImplementedError()

    def cv_results(self, x_data, y_data,cv=5):
        raise NotImplementedError()
    
    def predict(self):
        raise NotImplementedError()
        
        
    def cv_performance(self, y_true, y_pred):
        out = {}
        out['mse'] = metrics.mean_squared_error(y_true, y_pred)
        return out
        
        
    
class LinearRegressionModel(BaseRegressionModel):


    def train(self, x_data, y_data):

        clf = linear_model.LinearRegression()
        clf.fit(x_data, y_data)
        self.regression_model = clf
        return clf


    def cv_scores(self, x_data, y_data,cv=5):
        scores = cross_validation.cross_val_score(self.regression_model, x_data, y_data, cv=cv, score_func=self.cv_performance)
        score = [x['mse'] for x in scores]
        return list(score)
        
    
    def cv_results(self, x_data, y_data, k=5):
        
        #out = { 'predicted': [], 'observed' : []}
        out = []  
        
        kf = cross_validation.KFold(len(y_data), k, indices=False)
        for train, test in kf:
            x_d_train = x_data[train]
            x_d_test= x_data[test]
            y_d_train = y_data[train]
            y_d_test = y_data[test]
            
            clf = linear_model.LinearRegression()
            clf.fit(x_d_train, y_d_train)
            predictions = clf.predict(x_d_test)
            #out['predicted'].extend(list([float(x) for x in predictions]))
            #out['observed'].extend(list([float(x) for x in y_d_test]))
            
            for i,x in enumerate(predictions):
                item = [float(y_d_test[i]), float(x)]
                out.append(item)
            
        #print out
        return out
            
            
            
    
