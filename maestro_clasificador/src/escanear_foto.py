"""Convierte fotos de comprobantes en PDF estilo CamScanner (papel blanco, enderezado,
A4 con margen). Uso: procesar3(foto, salida_pdf, quad=[4 esquinas del documento]).
El usuario lo pidio asi (25/11/2026): mismo formato que CamScanner."""
import cv2, numpy as np
from PIL import Image
def order(p):
    p=np.array(p,dtype='float32'); s=p.sum(1); d=np.diff(p,axis=1).ravel()
    return np.array([p[np.argmin(s)],p[np.argmin(d)],p[np.argmax(s)],p[np.argmax(d)]],dtype='float32')
def find_quad(img):
    h,w=img.shape[:2]; k=1000/max(h,w); sm=cv2.resize(img,None,fx=k,fy=k)
    g=cv2.cvtColor(sm,cv2.COLOR_BGR2GRAY); g=cv2.GaussianBlur(g,(5,5),0)
    best=None
    # 1) papel vs fondo
    for e in (cv2.Canny(g,30,100), cv2.threshold(g,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]):
        e=cv2.dilate(e,np.ones((5,5),np.uint8))
        cs,_=cv2.findContours(e,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        for c in sorted(cs,key=cv2.contourArea,reverse=True)[:5]:
            a=cv2.approxPolyDP(c,0.02*cv2.arcLength(c,True),True)
            if len(a)==4 and cv2.contourArea(a)>0.35*sm.shape[0]*sm.shape[1]:
                best=a.reshape(4,2)/k; break
        if best is not None: break
    # 2) recuadro impreso (lineas largas)
    if best is None:
        th=cv2.adaptiveThreshold(g,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY_INV,25,10)
        hz=cv2.morphologyEx(th,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(sm.shape[1]//8,1)))
        vt=cv2.morphologyEx(th,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(1,sm.shape[0]//12)))
        m=cv2.dilate(hz|vt,np.ones((3,3),np.uint8))
        pts=cv2.findNonZero(m)
        if pts is not None:
            hull=cv2.convexHull(pts)
            a=cv2.approxPolyDP(hull,0.02*cv2.arcLength(hull,True),True)
            if len(a)==4: best=a.reshape(4,2)/k
            else: best=cv2.boxPoints(cv2.minAreaRect(pts))/k
    return order(best) if best is not None else None
def warp(img,q,pad=0.01):
    tl,tr,br,bl=q
    W=int(max(np.linalg.norm(br-bl),np.linalg.norm(tr-tl))); H=int(max(np.linalg.norm(tr-br),np.linalg.norm(tl-bl)))
    M=cv2.getPerspectiveTransform(q,np.array([[0,0],[W,0],[W,H],[0,H]],dtype='float32'))
    return cv2.warpPerspective(img,M,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
def deskew(img):
    g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    th=cv2.adaptiveThreshold(g,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY_INV,25,10)
    hz=cv2.morphologyEx(th,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(img.shape[1]//6,1)))
    L=cv2.HoughLinesP(hz,1,np.pi/1800,100,minLineLength=img.shape[1]//4,maxLineGap=20)
    if L is None: return img
    ang=[np.degrees(np.arctan2(y2-y1,x2-x1)) for x1,y1,x2,y2 in L.reshape(-1,4)]
    ang=[a for a in ang if abs(a)<10]
    if not ang: return img
    a=float(np.median(ang)); h,w=img.shape[:2]
    M=cv2.getRotationMatrix2D((w/2,h/2),a,1)
    return cv2.warpAffine(img,M,(w,h),flags=cv2.INTER_CUBIC,borderValue=(255,255,255))
def clean(img):
    # fondo blanco parejo, texto negro, tinta azul conservada (estilo CamScanner)
    f=img.astype(np.float32)
    g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    k=max(15,(min(img.shape[:2])//25)|1)
    bg=cv2.medianBlur(cv2.dilate(g,np.ones((7,7),np.uint8)),k).astype(np.float32)+1
    n=np.clip(f/bg[...,None],0,1)
    n=np.clip((n-0.50)/(0.88-0.50),0,1)**1.4
    out=(n*255).astype(np.uint8)
    hsv=cv2.cvtColor(out,cv2.COLOR_BGR2HSV).astype(np.float32)
    blue=(hsv[...,0]>95)&(hsv[...,0]<135)&(hsv[...,1]>60)
    hsv[...,1]=np.where(blue,np.clip(hsv[...,1]*1.4,0,255),hsv[...,1]*0.15)
    out=cv2.cvtColor(hsv.astype(np.uint8),cv2.COLOR_HSV2BGR)
    return cv2.filter2D(out,-1,np.array([[0,-.5,0],[-.5,3,-.5],[0,-.5,0]]))
def procesar(src,out,quad=None,trim=0.0):
    img=cv2.imread(src)
    q=np.array(quad,dtype='float32') if quad is not None else find_quad(img)
    if q is not None: img=warp(img,order(q))
    img=deskew(img)
    if trim: h,w=img.shape[:2]; t=int(trim*min(h,w)); img=img[t:h-t,t:w-t]
    img=clean(img)
    pil=Image.fromarray(cv2.cvtColor(img,cv2.COLOR_BGR2RGB))
    land=pil.width>pil.height; PW,PH=(3508,2480) if land else (2480,3508)
    m=int(0.07*PW); sc=min((PW-2*m)/pil.width,(PH-2*m)/pil.height)
    pil=pil.resize((int(pil.width*sc),int(pil.height*sc)),Image.LANCZOS)
    page=Image.new('RGB',(PW,PH),'white'); page.paste(pil,((PW-pil.width)//2,int(0.04*PH)))
    page.save(out,'PDF',resolution=300); return page

def frame_quad(img):
    h,w=img.shape[:2]; k=1200/max(h,w); sm=cv2.resize(img,None,fx=k,fy=k)
    g=cv2.cvtColor(sm,cv2.COLOR_BGR2GRAY)
    th=cv2.adaptiveThreshold(g,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY_INV,25,12)
    hz=cv2.morphologyEx(th,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(sm.shape[1]//5,1)))
    vt=cv2.morphologyEx(th,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(1,sm.shape[0]//6)))
    pts=cv2.findNonZero(hz|vt)
    hull=cv2.convexHull(pts).reshape(-1,2).astype(np.float32)
    s=hull.sum(1); d=hull[:,0]-hull[:,1]
    q=np.array([hull[np.argmin(s)],hull[np.argmax(d)],hull[np.argmax(s)],hull[np.argmin(d)]])
    return q/k
def deskew2(img):
    g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY); k=800/max(g.shape); sm=cv2.resize(g,None,fx=k,fy=k)
    th=cv2.adaptiveThreshold(sm,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY_INV,21,15)
    best=(0,-1); h,w=th.shape
    for a in np.arange(-8,8.01,0.2):
        M=cv2.getRotationMatrix2D((w/2,h/2),a,1); r=cv2.warpAffine(th,M,(w,h))
        v=np.var(r.sum(1))
        if v>best[1]: best=(a,v)
    a=best[0]; H,W=img.shape[:2]
    M=cv2.getRotationMatrix2D((W/2,H/2),a,1)
    return cv2.warpAffine(img,M,(W,H),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
def clean2(img):
    f=img.astype(np.float32); g=cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    k=max(21,(min(img.shape[:2])//20)|1)
    bg=cv2.medianBlur(cv2.dilate(g,np.ones((9,9),np.uint8)),k).astype(np.float32)+1
    n=np.clip(f/bg[...,None],0,1); n=np.clip((n-0.35)/(0.90-0.35),0,1)**1.25
    out=(n*255).astype(np.uint8)
    hsv=cv2.cvtColor(out,cv2.COLOR_BGR2HSV).astype(np.float32)
    blue=(hsv[...,0]>95)&(hsv[...,0]<135)&(hsv[...,1]>50)
    hsv[...,1]=np.where(blue,np.clip(hsv[...,1]*1.3,0,255),hsv[...,1]*0.1)
    out=cv2.cvtColor(hsv.astype(np.uint8),cv2.COLOR_HSV2BGR)
    return cv2.filter2D(out,-1,np.array([[0,-.25,0],[-.25,2,-.25],[0,-.25,0]]))
def procesar2(src,out,mode='frame',crop=None,margin=0.012):
    img=cv2.imread(src)
    if crop: x0,y0,x1,y1=crop; img=img[y0:y1,x0:x1]
    if mode=='frame':
        q=frame_quad(img); h,w=img.shape[:2]; mx=margin*w
        c=np.array([[-mx,-mx],[mx,-mx],[mx,mx],[-mx,mx]],np.float32); img=warp(img,(q+c).astype(np.float32))
    img=deskew2(img); img=clean2(img)
    pil=Image.fromarray(cv2.cvtColor(img,cv2.COLOR_BGR2RGB))
    land=pil.width>pil.height; PW,PH=(3508,2480) if land else (2480,3508)
    m=int(0.07*PW); sc=min((PW-2*m)/pil.width,(PH-2*m)/pil.height)
    pil=pil.resize((int(pil.width*sc),int(pil.height*sc)),Image.LANCZOS)
    page=Image.new('RGB',(PW,PH),'white'); page.paste(pil,((PW-pil.width)//2,int(0.04*PH)))
    page.save(out,'PDF',resolution=300); return page

def frame_quad2(img):
    h,w=img.shape[:2]; k=1200/max(h,w); sm=cv2.resize(img,None,fx=k,fy=k)
    g=cv2.cvtColor(sm,cv2.COLOR_BGR2GRAY)
    th=cv2.adaptiveThreshold(g,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY_INV,31,8)
    hz=cv2.morphologyEx(th,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(sm.shape[1]//10,1)))
    vt=cv2.morphologyEx(th,cv2.MORPH_OPEN,cv2.getStructuringElement(cv2.MORPH_RECT,(1,sm.shape[0]//10)))
    m=cv2.dilate(hz|vt,np.ones((5,5),np.uint8))
    cs,_=cv2.findContours(m,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    pts=np.vstack([c for c in cs if cv2.contourArea(c)>0.002*m.size or cv2.arcLength(c,False)>sm.shape[1]*0.4])
    hull=cv2.convexHull(pts)
    for e in np.arange(0.01,0.2,0.005):
        a=cv2.approxPolyDP(hull,e*cv2.arcLength(hull,True),True)
        if len(a)<=4: break
    if len(a)!=4: a=cv2.boxPoints(cv2.minAreaRect(hull))
    return order(a.reshape(-1,2)/k)

def procesar3(src,out,quad=None,crop=None,pad=12,skew=True):
    img=cv2.imread(src)
    if crop: x0,y0,x1,y1=crop; img=img[y0:y1,x0:x1]
    if quad is not None:
        q=order(quad); c=q.mean(0); q=q+np.sign(q-c)*pad
        img=warp(img,q.astype(np.float32))
    if skew: img=deskew2(img)
    img=clean2(img)
    pil=Image.fromarray(cv2.cvtColor(img,cv2.COLOR_BGR2RGB))
    land=pil.width>pil.height; PW,PH=(3508,2480) if land else (2480,3508)
    m=int(0.07*PW); sc=min((PW-2*m)/pil.width,(PH-2*m)/pil.height)
    pil=pil.resize((int(pil.width*sc),int(pil.height*sc)),Image.LANCZOS)
    page=Image.new('RGB',(PW,PH),'white'); page.paste(pil,((PW-pil.width)//2,int(0.04*PH)))
    page.save(out,'PDF',resolution=300); return page
