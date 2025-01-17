import itertools
from logging import raiseExceptions
from array_generator_cardio import *
import SimpleITK as sitk
import numpy as np
import cv2 as cv
from scipy.signal import convolve2d
import sys
from scipy import linalg
import matplotlib.pyplot as plt



tensor, objList = array_generator_cardio()

#Cropper Reference
totalOfImages = int(len(objList))
middleImage = int(totalOfImages/2)
referenceImage = ((objList[middleImage]).img)
referenceImage2 = referenceImage.astype(np.int8)
# ROI for Cropper method
roi = cv.selectROI('Crop the heart', referenceImage2)
print('Zoom ROI selected', roi)
cv.destroyAllWindows()
x1, x2, y1, y2 = int(roi[0]), int(roi[1]), int(roi[2]), int(roi[3])
heartview = referenceImage2[y1:int(y1 + y2), x1:int(x1 + x2)]
rois = cv.selectROIs('Select Lucas-Kanade windows', heartview)
cv.destroyAllWindows()



newList = []


for i in objList:
    normArr = i.normalize_image(np.array(i.img))
    crop = i.crop_array(normArr, roi)
    gradients = i.gradients_IxIy(crop, 3)
    setattr(i, 'Ix', gradients[0])
    setattr(i, 'Iy', gradients[1])
    setattr(i, 'cropped', crop)
    setattr(i, 'normArr', normArr)
    newList.append(i)
    

#Un atributo de cada objeto es el numero de phase cardiacas (esto te reeordena los objetitos)
cardPhase = int((newList[0]).cardPhase)
totalCardiacCycles = int(totalOfImages/cardPhase)
print('Cantidad de img = ', totalOfImages)
print("Cantidad de fases cardiacas = ", totalCardiacCycles)
# Lista de listas, cada ista tiene una fase entera cardiaca (generalmente 30 objetos c/u)
splitedList = np.array_split(newList, totalCardiacCycles)


class LucasKanadeData:
    def __init__(self, Ix1, Ix2, Iy1, Iy2, crop1, crop2):
        self.Ix1 = Ix1
        self.Ix2 = Ix2
        self.Iy1 = Iy1
        self.Iy2 = Iy2
        self.crop1 = crop1
        self.crop2 = crop2


i=0
iteratorList = []

with open('s.txt', 'w') as f:
    f.write(str(splitedList))

for i in splitedList:
    iterlist = list(itertools.pairwise(i))
    iteratorList.append(iterlist)
    
i=0
n=0
lkInstances = []


for i in iteratorList:
    for n in i:
        if not type((n[0]).cropped) is None:
            obj1 = n[0]
            obj2 = n[1]
            Ix1 = obj1.Ix
            Ix2 = obj2.Ix
            Iy1 = obj1.Iy
            Iy2 = obj2.Iy
            crop1 = obj1.cropped
            crop2 = obj2.cropped
            #print(type(obj1.cropped))
            instance = LucasKanadeData(Ix1, Ix2, Iy1, Iy2, crop1, crop2)
            lkInstances.append(instance)
        else:
            continue
        

for x in lkInstances:
    c1 = np.array(x.crop1)
    c2 = np.array(x.crop2)
    It = np.subtract(c2, c1)
    setattr(x, 'It', It)
    #img = sitk.GetImageFromArray(It)
    #myshow(img, cmap=plt.cm.bone)
    
    
def lucas_kanade_all(objList):
    
    vectors = []

    for i in objList:
        
        Ix1 = np.array(i.Ix1)
        Ix2 = np.array(i.Ix2)
        
        Iy1 = np.array(i.Iy1)
        Iy2 = np.array(i.Iy2)
        
        crop1 = np.array(i.crop1)
        crop2 = np.array(i.crop2)
        
        It = np.array(i.It)
        
        #print(np.shape(crop1))
        #print(np.shape(crop2))       
        
        A = np.hstack(Ix1)
        B = np.hstack(Iy1)
        
        S = np.column_stack((A, B))
        St = np.transpose(S)
        
        C = np.matmul(St, S)
        
        T = np.hstack(It)
        b = np.column_stack((T))

        #print(linalg.inv(C))
        #\print(linalg.det(C))
        #print(linalg.eigvals(C))
        
        #x = linalg.solve(S, b)
        var1 = linalg.inv(C)
        
    # print('It:', np.shape(It))
    # print('Ix:', np.shape(Ix1))
    # print('Iy:', np.shape(Iy1))
    # print('S:', np.shape(S))
    # print('St:', np.shape(St))
    # print('(St.S)inv:', np.shape(var1))
        
        var2 = np.matmul(St, T)
        x = np.matmul(var1, var2)
        
        vectors.append(x)
        
    normVectors = []
    #print(np.shape(x))
    for x in vectors:
        nor = np.linalg.norm(x)
        #print('norma', nor)
        if abs(nor) > 0: 
            normalized = x/nor
            normVectors.append(normalized)
        elif abs(nor) <= 0:
            normVectors.append(x)
            
    return normVectors
        
   
class Graphics():
    
    def __init__(self, crop, vectors):
        
        self.crop = crop
        self.vectors = vectors
        
        
    def grapher(crop, vectors):
        
        sh = np.shape(crop)
        
        x = np.arange(0, sh[0], 1)
        y = np.arange(0, sh[1], 1)
        X, Y = np.meshgrid(x, y)
        
        plt.figure()
        plt.streamplot(X, Y, vectors[0], vectors[1],
                       density=1, linewidth=None)
        plt.show()
        
        
    
    
vecs = lucas_kanade_all(lkInstances)

# with open('vectors.txt', 'w') as file:
#     for i in vecs:
#         file.write(str(i))
#         file.write('\n')