import torch
import argparse
import multiprocessing

def set_parser(parser):
    base_args = parser.add_argument_group('common arguments')
    base_args.add_argument(
        "--csv_path", type=str, default='./preprocessing/brave_data_label.csv',
        help="csv file path"
    )
    base_args.add_argument(
        "--iid", action="store_true", default=False, help="use argument for iid condition"
    )
    base_args.add_argument(
        "--test", action="store_true", default=False, help="Perform Test only"
    )
    base_args.add_argument(
        "--norm-type", type=int, choices=[0, 1, 2],
        help="0: ToTensor, 1: Ordinary image normalizaeion, 2: Image by Image normalization"
    )
    base_args.add_argument(
        "--batch-size", type=int, help="Batch size"
    )
    ae_args = parser.add_argument_group('Auto Encoder arguments')
    ae_args.add_argument(
        "--img-size", type=int, default=32, help='image size for Auto-encoder (default: 32x32)'
    )
    ae_args.add_argument(
        "--epochs", type=int, default=50, help="# of training epochs"
    )
    ae_args.add_argument(
        "--log-interval", type=int, default=200, help="Set interval for logging"
    )
    return parser

def get_config():
    """set arguments
    Returns:
        args -- [description]
    """
    parser = argparse.ArgumentParser(description="AE + SVR")
    args, _ = set_parser(parser).parse_known_args()
    args.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

    return args