"""Offline 3D object-handoff renderer. Technical preview ONLY.

Runs only when invoked explicitly, against a pre-existing --out directory.
Dependencies: vtk, numpy, pillow, FFmpeg. Never connects to YouTube.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import sys
import vtk
import numpy as np
from vtk.util.numpy_support import vtk_to_numpy
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from autopilot.character_motion import sample, ASHA, KABIR, shoulder

W,H,FPS=854,480,12

def actor(renderer,name,color,geometry,*,position=None):
    mapper=vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(geometry.GetOutputPort())
    ob=vtk.vtkActor()
    ob.SetMapper(mapper)
    ob.SetObjectName(name)
    ob.GetProperty().SetColor(*color)
    ob.GetProperty().SetSpecular(.26)
    ob.GetProperty().SetSpecularPower(30)
    if position is not None:ob.SetPosition(*position)
    renderer.AddActor(ob)
    return ob

def cube(renderer,name,dimensions,at,color):
    geo=vtk.vtkCubeSource()
    geo.SetXLength(dimensions[0]);geo.SetYLength(dimensions[1]);geo.SetZLength(dimensions[2])
    return actor(renderer,name,color,geo,position=at)

def ball(renderer,name,radius,at,color):
    geo=vtk.vtkSphereSource()
    geo.SetRadius(radius);geo.SetThetaResolution(18);geo.SetPhiResolution(14)
    return actor(renderer,name,color,geo,position=at)

def arm(renderer,name,color):
    geo=vtk.vtkCylinderSource();geo.SetRadius(.09);geo.SetHeight(1);geo.SetResolution(18)
    return actor(renderer,name,color,geo)

def place_limb(ob,a,b):
    pa=np.array(a,dtype=float);pb=np.array(b,dtype=float)
    d=pb-pa;n=np.linalg.norm(d)
    if n<.001:raise ValueError('Zero-length limb')
    u=np.array([0.,1.,0.]);normal=d/n;axis=np.cross(u,normal)
    transform=vtk.vtkTransform();transform.Translate(*((pa+pb)/2))
    dot=float(np.clip(u.dot(normal),-1,1))
    if np.linalg.norm(axis)>1e-6:
        transform.RotateWXYZ(float(np.degrees(np.arccos(dot))),*axis)
    elif dot<0:transform.RotateX(180)
    transform.Scale(1,n,1)
    ob.SetUserTransform(transform)

def build_scene(r):
    navy=(.04,.10,.17);metal=(.055,.17,.26);cyan=(.08,.70,.86)
    cube(r,'studio floor',(10,.12,6),(0,-.08,.6),navy)
    cube(r,'studio rear',(10,5,.16),(0,2.40,2.8),navy)
    for i in range(5):
        cube(r,'glass wall',(1.35,3.5,.10),(-3.7+i*1.85,2.6,2.65),(.065,.20,.29))
        cube(r,'light strip',(.025,3.6,.02),(-4.4+i*1.85,2.6,2.58),cyan)
    cube(r,'physical teaching table',(5,.13,1.75),(0,.93,-.8),metal)
    cube(r,'verification platform',(1.10,.12,.75),(-.35,1.03,-.41),(.065,.27,.34))
    for x in [-.8,.05]:cube(r,'platform cyan rail',(.025,.045,.75),(x,1.10,-.41),cyan)
    # Working 3D proxies, NOT production-cleared realistic rigs.
    people={}
    for name,x,shirt in [('asha',ASHA.x,(.16,.36,.62)),('kabir',KABIR.x,(.04,.38,.42)),('riya',1.75,(.08,.52,.42))]:
        root=(x,0,.18)
        ball(r,name+' face',.29,(x,2.35,.13),(.83,.57,.39))
        ball(r,name+' hair',.28,(x,2.54,.23),(.08,.07,.08))
        ball(r,name+' torso',.37,(x,1.56,.18),shirt)
        for side in (-1,1):ball(r,name+' eye',.034,(x+side*.12,2.37,-.15),(.01,.02,.03))
        people[name]=(root,shirt)
    arms={}
    for name,side,root in [('asha','right',ASHA),('kabir','left',KABIR)]:
        color=people[name][1]
        arms[name]=[arm(r,name+' upper',color),arm(r,name+' forearm',color),
                    ball(r,name+' hand',.13,(0,0,0),(.83,.57,.39)),root,side]
    warning=cube(r,'actual handed warning cube',(.24,.24,.24),(0,0,0),(.95,.26,.25))
    result=ball(r,'verified result',.20,(-.40,1.43,-.47),(.15,.86,.71))
    result.SetVisibility(False)
    cam=vtk.vtkCamera();r.SetActiveCamera(cam);cam.SetViewUp(0,1,0);cam.SetViewAngle(35)
    key=vtk.vtkLight();key.SetPosition(-3,5,-3);key.SetIntensity(1.8);r.AddLight(key)
    fill=vtk.vtkLight();fill.SetPosition(3,4,-2);fill.SetIntensity(.9);r.AddLight(fill)
    return cam,warning,result,arms

def run(out:Path):
    if not out.is_dir():raise ValueError('Output folder must already exist')
    renderer=vtk.vtkRenderer();renderer.SetBackground(.015,.040,.073)
    window=vtk.vtkRenderWindow();window.SetOffScreenRendering(True)
    window.SetSize(W,H);window.SetMultiSamples(0);window.AddRenderer(renderer)
    cam,warning,result,arms=build_scene(renderer)
    capture=vtk.vtkWindowToImageFilter();capture.SetInput(window)
    capture.SetInputBufferTypeToRGB();capture.ReadFrontBufferOff()
    dest=out/'flowminute_contact_repro.mp4'
    proc=subprocess.Popen(['ffmpeg','-nostdin','-hide_banner','-loglevel','error','-y',
       '-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}', '-r',str(FPS),'-i','-',
       '-c:v','libx264','-crf','23','-preset','veryfast','-pix_fmt','yuv420p',
       '-movflags','+faststart',str(dest)],stdin=subprocess.PIPE)
    try:
        for i in range(FPS*8):
            t=i/FPS;pose=sample(t)
            cam.SetPosition(-.6+.4*t/8,3.05,-9.0+.32*t/8)
            cam.SetFocalPoint(0,1.55,.03)
            for name,elbow,wrist in [('asha',pose.asha_elbow,pose.asha_wrist),
                                     ('kabir',pose.kabir_elbow,pose.kabir_wrist)]:
                top,fore,hand,root,side=arms[name]
                s=shoulder(root,side)
                place_limb(top,(s.x,s.y,s.z),(elbow.x,elbow.y,elbow.z))
                place_limb(fore,(elbow.x,elbow.y,elbow.z),(wrist.x,wrist.y,wrist.z))
                hand.SetPosition(wrist.x,wrist.y,wrist.z)
            warning.SetPosition(pose.cube.x,pose.cube.y,pose.cube.z)
            warning.SetVisibility(not pose.result_visible)
            result.SetVisibility(pose.result_visible)
            window.Render();capture.Modified();capture.Update()
            raw=vtk_to_numpy(capture.GetOutput().GetPointData().GetScalars())
            pixels=raw.reshape(H,W,3)[::-1].copy()
            im=Image.fromarray(pixels);draw=ImageDraw.Draw(im)
            draw.rounded_rectangle((20,H-75,W-20,H-18),radius=14,fill=(7,23,40))
            heading='A clue is not proof' if t<1.6 else ('Hand the clue to a reviewer' if t<4.85 else 'Verify before acting')
            draw.text((38,H-58),heading,fill=(235,248,251))
            proc.stdin.write(np.asarray(im).tobytes())
            if i in (0,35,70,95):im.save(out/f'contact_repro_frame_{i:03}.png')
    finally:
        if proc.stdin:proc.stdin.close()
        proc.wait(timeout=30)
    if proc.returncode:raise RuntimeError('ffmpeg did not finish')
    print('OFFLINE_PREVIEW_CREATED_NOT_RELEASE_READY',dest)

if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('--out',type=Path,required=True)
    args=cli.parse_args();run(args.out.resolve())
