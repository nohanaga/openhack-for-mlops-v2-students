
import argparse
import json
import mlflow
from mlflow.pyfunc import load_model
from mlflow.tracking import MlflowClient

def parse_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', type=str, help='Name under which model will be registered')
    parser.add_argument('--model_path', type=str, help='Model directory')
    parser.add_argument('--deploy_flag', type=str, help='A deploy flag whether to deploy or no')
    parser.add_argument('--eval_path', type=str, help='eval directory')
    
    args, _ = parser.parse_known_args()
    print(f'Arguments: {args}')

    return args


def main():

    args = parse_args()

    model_name = args.model_name
    model_path = args.model_path
    eval_path = args.eval_path

    mlflow.set_tag("model_name", model_name)
    mlflow.set_tag("model_path", model_path)

    # For information transfer between pipelines
    json_open = open(eval_path + "/output_evaluate.json", 'r')
    json_load = json.load(json_open)
    run_rmse = json_load["run_rmse"]
    run_r2 = json_load["run_r2"]
    deploy_flag = json_load["deploy_flag"]
    print("run_rmse: " + str(run_rmse))
    print("run_r2: " + str(run_r2))
    print("deploy_flag: " + str(deploy_flag))

    mlflow.set_tag("run_rmse", run_rmse)
    mlflow.set_tag("run_r2", run_r2)
    mlflow.set_tag("deploy_flag", deploy_flag)

    if deploy_flag==1:
        # Load model from model_path
        model = load_model(model_path + "/models") 
        # Log the sklearn model and register as version 1
        modelreg = mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="models",
            registered_model_name=model_name
        )
        print(modelreg)
        
        #Since log_model cannot register tags in models, use set_model_version_tag instead.
        client = MlflowClient() 
        model_info = client.get_registered_model(model_name)
        model_version = model_info.latest_versions[0].version
        dict_metrics =  {"RMSE": run_rmse, "R2": run_r2}
        client.set_model_version_tag(model_name, str(model_version), "metrics", json.dumps(dict_metrics))
        print("Model registered!")
    else:
        print("Model will not be registered!")

if __name__ == "__main__":
    main()
