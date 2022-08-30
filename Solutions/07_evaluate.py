
import argparse
import json
import mlflow
from mlflow.pyfunc import load_model
from mlflow.tracking import MlflowClient

def parse_args():

    parser = argparse.ArgumentParser()
    parser.add_argument('--model_name', type=str, help='Name under which model will be registered')
    parser.add_argument('--model_path', type=str, help='Model directory')
    parser.add_argument('--output_path', type=str, help="eval output", default='./outputs')

    args, _ = parser.parse_known_args()
    print(f'Arguments: {args}')

    return args

def main():

    args = parse_args()

    model_name = args.model_name
    model_path = args.model_path
    output_path = args.output_path
    deploy_flag = 0
    
    mlflow.set_tag("model_name", model_name)
    mlflow.set_tag("model_path", model_path)

    # For information transfer between pipelines
    json_open = open(model_path + "/metric.json", 'r')
    json_load = json.load(json_open)
    # Get accuracy (RMSE) from previous step Run
    run_rmse = json_load["RMSE"]
    print("run_rmse: " + str(run_rmse))
    run_r2 = json_load["R2"]
    print("run_r2: " + str(run_r2))

    run_id = json_load["run_id"]
    print("train run_id: " + str(run_id))
    # Get Run executed before
    finished_mlflow_run = mlflow.get_run(run_id)
    # Pull metrics and tags from Run
    metrics = finished_mlflow_run.data.metrics
    print(metrics)

    output_info = {
        'run_rmse' : run_rmse,
        'model_rmse' : 0,
        'deploy_flag' : deploy_flag,
    }

    try:
        # Get the latest registered models
        client = MlflowClient() 
        model_info = client.get_registered_model(model_name)
        print("model_info: " + str(model_info.latest_versions[0]))
        model_tags = model_info.latest_versions[0].tags
        json_metrics = json.loads(model_tags["metrics"])

        # Model accuracy (RMSE)
        model_rmse = json_metrics["RMSE"]
        output_info['model_rmse'] = model_rmse
        print("model_rmse: " + str(model_rmse))
        
        # RMSE Comparison
        if run_rmse < model_rmse:
            print("Improved accuracy. 精度が上回りました")
            deploy_flag = 1

        else:
            print("Accuracy did not improve. 精度が上回りませんでした")
            deploy_flag = 0
    
    except:
        print("No model exists. Register the model as it is.　モデルが存在しません。そのまま登録します。")
        deploy_flag = 1

    output_info['run_rmse'] = run_rmse
    output_info['run_r2'] = run_r2
    output_info['deploy_flag'] = deploy_flag
    mlflow.set_tag("deploy_flag", deploy_flag)

    output_json = json.dumps(output_info)
    with open(output_path + "/output_evaluate.json", "w") as f:
        f.write(output_json)

    mlflow.log_artifact(output_path)

if __name__ == "__main__":
    main()
