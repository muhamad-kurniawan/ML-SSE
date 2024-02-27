from utilities import featurization as fzn
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np
import scipy


from warnings import simplefilter
simplefilter(action='ignore', category=FutureWarning)

class TECRF:
    def __init__(self, parameters='default'):
        param_default = {
                'rf1':[None, 300],
                'rf2':[-2.2, 150],
                'rf3':[-2.1, 150],
                'rf4':[-2, 150],
            }
        if parameters=='default':
            self.params = param_default
        else:
            self.params=parameters
        
        self.lambdas, self.n_estimators_ = [v[0] for v in list(self.params.values())], [v[1] for v in list(self.params.values())]

    def feature_engineering(self, train_formulas, train_target, lambda_):
        if lambda_==None:
            schemes=['avg','dev', 'max','min','range']
        else:
            schemes=['avg_yj','dev_yj', 'max','min','range']
        return fzn.apply_scheme(train_formulas, train_target, schemes=schemes, lambda_transform=lambda_)
    
    def train(self, train, val):
        train_formulas = train['formula']
        train_targets = train['target']
        
        val_formulas = val['formula']
        val_targets = val['target']
        
        self.models = []
        self.weights = []
        predictions = []
        error_models = []

        for n in range(len(self.lambdas)):
#             reg = RandomForestRegressor(n_estimators=self.n_estimators_[n], bootstrap=False)
            reg = RandomForestRegressor(random_state = 1, n_estimators= self.n_estimators_[n], min_samples_split= 5, min_samples_leaf= 2, max_features= 'sqrt', max_depth= 50, bootstrap= False)
            # reg = RandomForestRegressor(random_state = 1, n_estimators= self.n_estimators_[n], min_samples_split= 5, min_samples_leaf= 2, max_depth= 50, bootstrap= True)

            X_train, y_train, formulas_train = self.feature_engineering(train_formulas, train_targets, lambda_=self.lambdas[n])
            X_val, y_val, formulas_val = self.feature_engineering(val_formulas, val_targets, lambda_=self.lambdas[n])
            reg.fit(X_train, y_train)
            
            prediction_trees = []
            error_trees = []
            
            # predict and find error for each trees
            for tree in range(self.n_estimators_[n]):
                pred = reg.estimators_[tree].predict(X_val)
                prediction_trees.append(pred)
                # error = mean_squared_error(y_val, pred, squared=False)
                # error = mean_absolute_error(y_val, pred)
                error = r2_score(y_val, pred)
                error_trees.append(error)
                
            predictions.append(prediction_trees)
            error_models.append(error_trees)
            self.models.append(reg)
            
        #calculate weights
        
        errors_flattened = [e2 for e1 in error_models for e2 in e1]
        # print(errors_flattened)
        preds_flattened = [p2 for p1 in predictions for p2 in p1]
        
        # logistic_scores = 1 / (1 + np.exp(-np.array(errors_flattened)))
        # self.weights = logistic_scores / np.sum(logistic_scores)

        power_scores = np.power(np.array(errors_flattened), 2)
        self.weights = power_scores / np.sum(power_scores)

        # scaled_scores = np.exp(0.4 * np.array(errors_flattened))
        # self.weights = scaled_scores / np.sum(scaled_scores)

        # self.weights = np.array(errors_flattened) / np.sum(np.array(errors_flattened))
        # self.weights = [1]*len(errors_flattened)

        # self.weights = scipy.special.softmax(errors_flattened)
        print(self.weights)

    def predict(self, data):
        formulas = data['formula']
        targets = data['target']
        predictions = []
        
        for n in range(len(self.models)):        
            prediction_trees = []
            X, y, formulas = self.feature_engineering(formulas, targets, self.lambdas[n])
            for tree in range(self.n_estimators_[n]):
                pred = self.models[n].estimators_[tree].predict(X)
                prediction_trees.append(pred)
                
            predictions.append(prediction_trees)
        
        preds_flattened = [p2 for p1 in predictions for p2 in p1]
        print(np.array(preds_flattened).T.shape)
        print(len(self.weights))
        final_pred = [np.average(x, weights=self.weights) for x in np.array(preds_flattened).T]
        # final_pred = [np.average(x) for x in np.array(preds_flattened).T]
        
        return final_pred