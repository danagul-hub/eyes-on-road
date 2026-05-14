# !8AB5<0 :;0AA8D8:0F88 A>AB>O=8O 3;07

@>5:B @0745;5= =0 B@8 >A=>2=KE D09;0 4;O C4>1=>3> @0745;5=8O >1CG5=8O 8 8=D5@5=A0.

## !B@C:BC@0 ?@>5:B0

- **`train.py`** - 1CG5=85 <>45;8
- **`infer.py`** - =D5@5=A (?@54A:070=8O) 157 ?5@5>1CG5=8O  
- **`main_fast.py`** - #=825@A0;L=K9 70?CA: A 2K1>@>< @568<0
- **`images/`** - 0?:0 A 40B0A5B0<8 (zip D09;K)
- **`lol.xml`** - 0A:04=K9 :;0AA8D8:0B>@ 4;O 45B5:F88 3;07

## A?>;L7>20=85

### 1. 1CG5=85 <>45;8
```bash
python train.py
```
8;8
```bash
python main_fast.py --mode train
```

### 2. =D5@5=A A 251-:0<5@K
```bash
python infer.py --webcam
```
8;8
```bash
python main_fast.py --mode infer
```

### 3. =0;87 87>1@065=8O
```bash
python infer.py --image path/to/image.jpg
```

### 4. =B5@0:B82=K9 @568<
```bash
python main_fast.py
```

## $09;K <>45;8

>A;5 >1CG5=8O A>740NBAO D09;K:
- `eye_classifier.pkl` - >1CG5==0O <>45;L
- `eye_scaler.pkl` - =>@<0;870B>@ 40==KE
- `class_mapping.pkl` - <0??8=3 :;0AA>2

## ;0AAK

>45;L @07;8G05B 3 A>AB>O=8O 3;07:
- **;0AA 0**: Close Eyes (70:@KBK5 3;070)
- **;0AA 1**: Drowsy (A>==K5 3;070) 
- **;0AA 2**: Open Eyes (>B:@KBK5 3;070)

## "@51>20=8O

- Python 3.7+
- OpenCV
- scikit-learn
- numpy
- joblib
- tqdm

## A>15==>AB8

- 2B><0B8G5A:>5 >1=0@C65=85 8 >1@01>B:0 zip 0@E82>2 2 ?0?:5 `images`
- >445@6:0 @07;8G=KE D>@<0B>2 87>1@065=89 (jpg, png, bmp)
- ?B8<878@>20==0O 45B5:F8O 3;07 4;O @07=KE @07@5H5=89
- =B5@0:B82=K9 @568< A 251-:0<5@>9
- >7<>6=>ABL 0=0;870 >B45;L=KE 87>1@065=89
